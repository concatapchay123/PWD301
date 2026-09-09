"""Security and IDOR Negative Tests for Assessment Attempt Delivery (TASK-013)."""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from flask import Flask
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.assessment import Assessment
from pwd301.models.course import Course
from pwd301.models.identity import Role, User
from pwd301.services.assessment_service import (
    assign_question,
    create_assessment,
    create_section,
    publish_assessment,
)
from pwd301.services.attempt_service import (
    get_attempt_delivery,
    start_assessment_attempt,
)
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.exceptions import ForbiddenError
from pwd301.services.question_bank_service import create_question
from pwd301.services.user_service import assign_role_to_user, register_user

UUID_REGEX = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _assert_zero_leakage(data: Any) -> None:
    """Recursively verify that no correct answers, secret explanations, or BIGINT PKs leak."""
    if isinstance(data, dict):
        for k, v in data.items():
            assert k != "is_correct", f"Security violation: 'is_correct' leaked in {data}"
            assert k != "explanation", f"Security violation: 'explanation' leaked in {data}"
            assert k != "source_choice_id", (
                f"Security violation: 'source_choice_id' leaked in {data}"
            )
            assert k != "source_question_id", (
                f"Security violation: 'source_question_id' leaked in {data}"
            )
            assert k != "creator_user_id", f"Internal FK 'creator_user_id' leaked in {data}"
            assert k != "student_user_id", f"Internal FK 'student_user_id' leaked in {data}"

            if (
                k in ("attempt_id", "assessment_id", "attempt_question_id", "choice_key")
                and v is not None
            ):
                assert isinstance(v, str), f"Field '{k}' must be UUID string, got {type(v)}"
                assert UUID_REGEX.match(v), f"Field '{k}' is not valid UUID: {v}"

            _assert_zero_leakage(v)
    elif isinstance(data, list):
        for item in data:
            _assert_zero_leakage(item)


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
    """Ensure standard roles exist in test database."""
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
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create administrator user."""
    u = register_user("admin_idor@example.com", "Password@123", "Admin User")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create instructor owner."""
    u = register_user("inst_idor@example.com", "Password@123", "Instructor User")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def other_instructor(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create unrelated instructor user."""
    u = register_user("other_inst_idor@example.com", "Password@123", "Other Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_a(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create student A."""
    u = register_user("student_a_idor@example.com", "Password@123", "Student A")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def student_b(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create student B."""
    u = register_user("student_b_idor@example.com", "Password@123", "Student B")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def published_course(app: Flask, instructor_user: User, admin_user: User) -> Course:
    """Create and publish course."""
    c = create_course(
        instructor_user,
        {"course_code": "SEC-101", "title": "Network Security"},
    )
    change_course_status(instructor_user, c.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin_user, c.id, "APPROVED")
    change_course_status(admin_user, c.id, "PUBLISHED")
    db.session.commit()
    return c


@pytest.fixture
def published_assessment(
    app: Flask,
    instructor_user: User,
    published_course: Course,
) -> Assessment:
    """Create and publish assessment with questions."""
    now = datetime.now(UTC)
    payload = {
        "title": "Security Quiz 1",
        "assessment_type": "QUIZ",
        "time_limit_minutes": 45,
        "attempt_limit": 2,
        "open_at": (now - timedelta(hours=1)).isoformat(),
        "close_at": (now + timedelta(days=1)).isoformat(),
    }
    assessment = create_assessment(
        instructor_user, published_course.id, payload, session=db.session
    )
    sec = create_section(
        instructor_user,
        assessment.public_id,
        {"title": "Section 1", "position": 1},
        session=db.session,
    )
    db.session.commit()

    q_payload = {
        "question_type": "SINGLE_CHOICE",
        "difficulty": "REMEMBER",
        "content": "What is an IDOR vulnerability?",
        "explanation": "Insecure Direct Object Reference occurs when authorization is missing.",
        "default_points": 10.0,
        "choices": [
            {"content": "Broken Access Control", "is_correct": True, "position": 1},
            {"content": "SQL Injection", "is_correct": False, "position": 2},
        ],
        "provenance": {"source_type": "MANUAL", "notes": "Security test"},
    }
    q = create_question(instructor_user, published_course.id, q_payload, session=db.session)
    db.session.commit()
    assign_question(
        instructor_user,
        assessment.public_id,
        {"question_id": str(q.public_id), "section_id": sec.id, "points": 10.0},
        session=db.session,
    )
    publish_assessment(instructor_user, assessment.public_id, session=db.session)
    db.session.commit()
    return assessment


# ============================================================================
# SECURITY & IDOR TESTS
# ============================================================================


def test_student_b_cannot_view_student_a_attempt(
    app: Flask,
    published_assessment: Assessment,
    published_course: Course,
    student_a: User,
    student_b: User,
) -> None:
    """Student B must be rejected when attempting to view Student A's attempt (IDOR Defense)."""
    # Enroll both students
    enroll_student(student_a, published_course.id, session=db.session)
    enroll_student(student_b, published_course.id, session=db.session)
    db.session.commit()

    # Student A starts attempt
    attempt_a, _ = start_assessment_attempt(
        student_a, published_assessment.public_id, session=db.session
    )
    db.session.commit()

    # Student A can access own attempt delivery
    delivery_a = get_attempt_delivery(student_a, attempt_a.public_id, session=db.session)
    assert delivery_a["attempt_id"] == str(attempt_a.public_id)

    # Student B trying to access Student A's attempt must be denied with ForbiddenError
    with pytest.raises(ForbiddenError, match="do not have permission"):
        get_attempt_delivery(student_b, attempt_a.public_id, session=db.session)


def test_unrelated_instructor_cannot_view_student_attempt(
    app: Flask,
    published_assessment: Assessment,
    published_course: Course,
    student_a: User,
    other_instructor: User,
) -> None:
    """An instructor who does NOT manage the course cannot access the student attempt."""
    enroll_student(student_a, published_course.id, session=db.session)
    db.session.commit()

    attempt_a, _ = start_assessment_attempt(
        student_a, published_assessment.public_id, session=db.session
    )
    db.session.commit()

    with pytest.raises(ForbiddenError, match="do not have permission"):
        get_attempt_delivery(other_instructor, attempt_a.public_id, session=db.session)


def test_admin_oversight_can_view_attempt(
    app: Flask,
    published_assessment: Assessment,
    published_course: Course,
    student_a: User,
    admin_user: User,
) -> None:
    """Platform administrator has authorized oversight to view student attempts."""
    enroll_student(student_a, published_course.id, session=db.session)
    db.session.commit()

    attempt_a, _ = start_assessment_attempt(
        student_a, published_assessment.public_id, session=db.session
    )
    db.session.commit()

    delivery = get_attempt_delivery(admin_user, attempt_a.public_id, session=db.session)
    assert delivery["attempt_id"] == str(attempt_a.public_id)


def test_delivery_payload_zero_leakage(
    app: Flask,
    published_assessment: Assessment,
    published_course: Course,
    student_a: User,
) -> None:
    """Verify delivery payload does not leak is_correct, explanation, or internal PKs."""
    enroll_student(student_a, published_course.id, session=db.session)
    db.session.commit()

    attempt_a, _ = start_assessment_attempt(
        student_a, published_assessment.public_id, session=db.session
    )
    db.session.commit()

    delivery = get_attempt_delivery(student_a, attempt_a.public_id, session=db.session)
    _assert_zero_leakage(delivery)

    # Explicit checks on questions and choices
    for q in delivery["questions"]:
        assert "is_correct" not in q
        assert "explanation" not in q
        assert "source_question_id" not in q
        for c in q["choices"]:
            assert "is_correct" not in c
            assert "source_choice_id" not in c
