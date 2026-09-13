"""Security and anti-cheat tests for cross-timezone assessment synchronization."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from flask import Flask
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course
from pwd301.models.identity import Role, User
from pwd301.services.assessment_service import (
    _parse_iso_datetime,
    assign_question,
    create_assessment,
    create_section,
    publish_assessment,
)
from pwd301.services.attempt_service import start_assessment_attempt
from pwd301.services.course_service import create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.exceptions import AssessmentNotOpenError
from pwd301.services.question_bank_service import create_question
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def test_instructor(app: Flask) -> User:
    """Create a verified instructor user."""
    sess: Session = db.session
    role = sess.query(Role).filter(Role.code == "INSTRUCTOR").first()
    if not role:
        role = Role(code="INSTRUCTOR", name="Instructor")
        sess.add(role)
        sess.commit()
    u = register_user("inst_tz@example.com", "Password@123", "Instructor Timezone")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def test_student(app: Flask) -> User:
    """Create a student user."""
    return register_user("stud_tz@example.com", "Password@123", "Student Timezone")


@pytest.fixture
def test_course(app: Flask, test_instructor: User) -> Course:
    """Create and publish a course."""
    c = create_course(
        test_instructor,
        {
            "course_code": "TZ101",
            "title": "Timezone Synchronization Security Course",
            "summary": "Anti-Cheat Global Exam Course",
        },
    )
    c.status = "PUBLISHED"
    db.session.commit()
    return c


def test_cross_timezone_simultaneous_access_control(
    app: Flask,
    test_instructor: User,
    test_student: User,
    test_course: Course,
) -> None:
    """Validate that regardless of instructor or student timezone, server-authoritative

    UTC enforces an unbypassable simultaneous exam window (Anti-Cheat).
    """
    enroll_student(test_student, test_course.id, session=db.session)

    # 1. Instructor in GMT+1 configures assessment:
    # Set to open in 2 hours according to GMT+1 (e.g. 14:00 GMT+1)
    now_utc = datetime.now(UTC)
    future_open_gmt1_str = (now_utc + timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%S")
    open_at_utc = _parse_iso_datetime(future_open_gmt1_str, "open_at", tz_offset_str="+01:00")

    payload = {
        "title": "Anti-Cheat Global Exam",
        "description": "Cross-timezone exam test",
        "assessment_type": "EXAM",
        "scoring_policy": "HIGHEST",
        "time_limit_minutes": 60,
        "open_at": future_open_gmt1_str,
        "close_at": (now_utc + timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%S"),
        "timezone_offset": "+01:00",
    }
    asm = create_assessment(test_instructor, test_course.id, payload, session=db.session)
    from pwd301.services.assessment_service import _normalize_dt

    assert _normalize_dt(asm.open_at) == open_at_utc

    sec = create_section(
        test_instructor,
        asm.public_id,
        {"title": "Section 1", "position": 1},
        session=db.session,
    )
    q_payload = {
        "question_type": "SINGLE_CHOICE",
        "difficulty": "REMEMBER",
        "content": "Is server time authoritative in UTC?",
        "explanation": "Yes, server time enforces anti-cheat.",
        "default_points": 10.0,
        "choices": [
            {"key": "A", "content": "Yes", "is_correct": True, "position": 1},
            {"key": "B", "content": "No", "is_correct": False, "position": 2},
        ],
        "provenance": {"source_type": "MANUAL"},
    }
    q = create_question(test_instructor, test_course.id, q_payload, session=db.session)
    assign_question(
        test_instructor,
        asm.public_id,
        {"question_id": str(q.public_id), "section_id": sec.id, "points": 10.0},
        session=db.session,
    )
    publish_assessment(test_instructor, asm.public_id, session=db.session)
    db.session.commit()

    # 2. Student in Vietnam (GMT+7) tries to access early before UTC open time
    # MUST fail closed with AssessmentNotOpenError
    with pytest.raises(AssessmentNotOpenError, match="not yet open"):
        start_assessment_attempt(test_student, asm.public_id, session=db.session)

    # 3. Simulate time arriving inside the window
    asm.open_at = now_utc - timedelta(minutes=10)
    asm.close_at = now_utc + timedelta(minutes=50)
    db.session.commit()

    # Student starts successfully inside the window
    att, raw_token = start_assessment_attempt(test_student, asm.public_id, session=db.session)
    assert att.status == "IN_PROGRESS"
    assert att.deadline_at is not None
    assert _normalize_dt(att.deadline_at) > now_utc
