"""Unit tests for Server-Authoritative Wall-Clock Heartbeat & Anti-Bypass Security (TASK-085)."""

import json
import time
from typing import Any
import pytest
from flask import Flask

from pwd301.extensions import db
from pwd301.models.course import Course, Enrollment, EnrollmentPeriod, Lesson, LessonProgress
from pwd301.models.identity import Role, User
from pwd301.models.notification_audit import AuditEvent
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.exceptions import LessonValidationError, LessonStateViolationError
from pwd301.services.lesson_service import (
    create_lesson,
    record_lesson_progress,
)
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
    sess = db.session
    role_map: dict[str, Role] = {}
    for code, name in [
        ("ADMIN", "System Administrator"),
        ("INSTRUCTOR", "Course Instructor"),
        ("STUDENT", "Enrolled Student"),
    ]:
        role = sess.query(Role).filter_by(code=code).first()
        if not role:
            role = Role(code=code, name=name)
            sess.add(role)
            sess.flush()
        role_map[code] = role
    sess.commit()
    return role_map


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    u = register_user("wc_instructor@example.com", "Password@123", "WC Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    return register_user("wc_student1@example.com", "Password@123", "WC Student 1")


@pytest.fixture
def course_sample(app: Flask, instructor_user: User) -> Course:
    return create_course(
        instructor_user,
        {
            "course_code": "SEC-WC-101",
            "title": "Anti-Bypass Wall-Clock Course",
            "description": "Course for wall-clock testing",
            "subject_area": "Security",
            "level": "BEGINNER",
        },
    )



def test_cannot_bypass_minimum_duration_with_high_view_fraction(
    app: Flask,
    instructor_user: User,
    student_user: User,
    course_sample: Course,
) -> None:
    """Zero-Trust Iron Law: High view_fraction CANNOT artificially promote seconds_spent or complete lesson."""
    sess = db.session

    admin = register_user("wc_admin1@example.com", "Password@123", "WC Admin 1")
    admin = assign_role_to_user(admin.id, "ADMIN")
    change_course_status(instructor_user, course_sample.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin, course_sample.id, "APPROVED")
    change_course_status(instructor_user, course_sample.id, "PUBLISHED")

    # Create lesson requiring 300 seconds and 90% watch
    lesson = create_lesson(
        instructor_user,
        course_sample.id,
        {
            "title": "Anti-Bypass Protected Video Lesson",
            "markdown_content": "<!-- video_url: https://example.com/stream.m3u8 -->\n\nNội dung bài học.",
            "minimum_completion_seconds": 300,
            "viewed_fraction_required": 0.90,
            "status": "PUBLISHED",
        },
    )

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

    # An attacker or script attempts to send view_fraction=0.95 with only seconds_increment=5
    p1 = record_lesson_progress(
        actor=student_user,
        lesson_id=lesson.id,
        seconds_increment=5,
        view_fraction=0.95,
    )

    # Must NOT have jumped to 300s!
    assert p1.seconds_spent == 5, f"Expected 5 seconds spent, got {p1.seconds_spent}"
    assert float(p1.max_view_fraction) == 0.95
    assert p1.completed_at is None, "Lesson must NOT be marked completed without fulfilling 300 seconds wall-clock time!"


def test_rapid_ping_spam_is_capped_by_server_wall_clock(
    app: Flask,
    instructor_user: User,
    student_user: User,
    course_sample: Course,
) -> None:
    """A client cannot gain 60 seconds of progress in 0.1 seconds of physical time."""
    sess = db.session

    admin = register_user("wc_admin2@example.com", "Password@123", "WC Admin 2")
    admin = assign_role_to_user(admin.id, "ADMIN")
    change_course_status(instructor_user, course_sample.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin, course_sample.id, "APPROVED")
    change_course_status(instructor_user, course_sample.id, "PUBLISHED")

    lesson = create_lesson(
        instructor_user,
        course_sample.id,
        {
            "title": "Pacing Verification Lesson",
            "markdown_content": "# Lesson Content",
            "minimum_completion_seconds": 60,
            "viewed_fraction_required": 0.80,
            "status": "PUBLISHED",
        },
    )

    user2 = register_user("wc_student2@example.com", "Password@123", "WC Student 2")
    user2 = assign_role_to_user(user2.id, "STUDENT")
    enrollment2 = Enrollment(
        student_user_id=user2.id,
        course_id=course_sample.id,
        status="ACTIVE",
    )
    sess.add(enrollment2)
    sess.flush()
    period2 = EnrollmentPeriod(
        enrollment_id=enrollment2.id,
        period_no=1,
        status="ACTIVE",
    )
    sess.add(period2)
    sess.flush()
    enrollment2.current_period_id = period2.id
    sess.commit()

    # First ping: 10s
    p1 = record_lesson_progress(
        actor=user2,
        lesson_id=lesson.id,
        seconds_increment=10,
        view_fraction=0.20,
    )
    assert p1.seconds_spent == 10

    # Attacker immediately fires another ping 50ms later claiming 60s
    p2 = record_lesson_progress(
        actor=user2,
        lesson_id=lesson.id,
        seconds_increment=60,
        view_fraction=0.50,
        enforce_wall_clock=True,
    )
    # The second ping arrived almost instantly (less than 1s elapsed)
    # The server must NOT credit 60 seconds; it must cap to actual elapsed wall-clock time
    assert p2.seconds_spent < 20, f"Spam ping was credited unexpectedly high: {p2.seconds_spent}"

    # Verify AuditEvent was persisted for the anomaly
    anomaly_event = (
        sess.query(AuditEvent)
        .filter(
            AuditEvent.action == "LESSON_PROGRESS_PACE_ANOMALY",
            AuditEvent.actor_user_id == user2.id,
        )
        .first()
    )
    assert anomaly_event is not None, "Expected LESSON_PROGRESS_PACE_ANOMALY audit event to be logged!"
