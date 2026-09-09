"""Security & IDOR Negative Tests for Attempt Lease Management (TASK-014).

Validates:
- Strict zero-trust object-level authorization on lease mutations (heartbeat, takeover, release).
- Enrolled peer students are blocked with ForbiddenError (403).
- Course instructors are blocked with ForbiddenError (403) from manipulating student leases.
- Token masking: only SHA-256 binary hash is stored; raw 32-byte hex token is never
  persisted or leaked.
- ADR-002: no internal BIGINT primary/foreign keys leaked in lease operations.
"""

from __future__ import annotations

import hashlib
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
    _serialize_attempt,
    release_attempt_lease,
    renew_attempt_lease,
    start_assessment_attempt,
    takeover_attempt_lease,
)
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.exceptions import ForbiddenError
from pwd301.services.question_bank_service import create_question
from pwd301.services.user_service import assign_role_to_user, register_user


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
    u = register_user("admin_lease_sec@example.com", "Password@123", "Admin User")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create instructor user."""
    u = register_user("inst_lease_sec@example.com", "Password@123", "Attempt Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_owner(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create student owner of attempt."""
    u = register_user("student_owner_sec@example.com", "Password@123", "Attempt Owner")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def peer_student(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create peer student enrolled in same course."""
    u = register_user("peer_student_sec@example.com", "Password@123", "Peer Student")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def published_course(app: Flask, instructor_user: User, admin_user: User) -> Course:
    """Create and publish a course owned by instructor."""
    c = create_course(
        instructor_user,
        {
            "course_code": "LEASE-SEC-101",
            "title": "Lease Security Course",
            "summary": "Security Test Course",
        },
    )
    change_course_status(instructor_user, c.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin_user, c.id, "APPROVED")
    change_course_status(admin_user, c.id, "PUBLISHED")
    db.session.commit()
    return c


@pytest.fixture
def enrolled_students(
    app: Flask,
    student_owner: User,
    peer_student: User,
    published_course: Course,
) -> tuple[User, User]:
    """Enroll both student owner and peer student into the published course."""
    enroll_student(student_owner, published_course.id, session=db.session)
    enroll_student(peer_student, published_course.id, session=db.session)
    db.session.commit()
    return student_owner, peer_student


def _make_assessment_with_question(instructor: User, course: Course) -> Assessment:
    """Helper to create and publish an assessment with one assigned question."""
    now = datetime.now(UTC)
    payload = {
        "title": "Security Lease Assessment",
        "assessment_type": "QUIZ",
        "time_limit_minutes": 60,
        "open_at": (now - timedelta(hours=1)).isoformat(),
        "close_at": (now + timedelta(hours=24)).isoformat(),
        "passing_score": 50.0,
    }
    assessment = create_assessment(instructor, course.id, payload, session=db.session)
    section = create_section(
        instructor, assessment.id, {"title": "Main Section"}, session=db.session
    )

    q_payload: dict[str, Any] = {
        "question_type": "SINGLE_CHOICE",
        "difficulty": "REMEMBER",
        "content": "Is lease single-user?",
        "default_points": 10.0,
        "choices": [
            {"content": "Yes", "is_correct": True, "position": 1},
            {"content": "No", "is_correct": False, "position": 2},
        ],
        "provenance": {"source_type": "MANUAL"},
    }
    q = create_question(instructor, course.id, q_payload, session=db.session)
    assign_question(
        instructor,
        assessment.id,
        {"question_id": q.id, "points": 10.0, "section_id": section.id},
        session=db.session,
    )
    publish_assessment(instructor, assessment.id, session=db.session)
    db.session.commit()
    return assessment


def test_peer_student_cannot_heartbeat_victim_lease(
    app: Flask,
    enrolled_students: tuple[User, User],
    instructor_user: User,
    published_course: Course,
) -> None:
    """Verify enrolled peer student cannot renew victim's attempt lease (403 Forbidden)."""
    owner, peer = enrolled_students
    assessment = _make_assessment_with_question(instructor_user, published_course)
    attempt, token = start_assessment_attempt(owner, assessment.id, session=db.session)

    with pytest.raises(ForbiddenError, match="permission to manage this assessment attempt lease"):
        renew_attempt_lease(
            actor=peer,
            attempt_id=attempt.id,
            raw_lease_token=token,
            session=db.session,
        )


def test_peer_student_cannot_takeover_victim_lease(
    app: Flask,
    enrolled_students: tuple[User, User],
    instructor_user: User,
    published_course: Course,
) -> None:
    """Verify enrolled peer student cannot take over victim's attempt lease (403 Forbidden)."""
    owner, peer = enrolled_students
    assessment = _make_assessment_with_question(instructor_user, published_course)
    attempt, _ = start_assessment_attempt(owner, assessment.id, session=db.session)

    with pytest.raises(ForbiddenError, match="permission to manage this assessment attempt lease"):
        takeover_attempt_lease(
            actor=peer,
            attempt_id=attempt.id,
            session=db.session,
        )


def test_peer_student_cannot_release_victim_lease(
    app: Flask,
    enrolled_students: tuple[User, User],
    instructor_user: User,
    published_course: Course,
) -> None:
    """Verify enrolled peer student cannot release victim's attempt lease (403 Forbidden)."""
    owner, peer = enrolled_students
    assessment = _make_assessment_with_question(instructor_user, published_course)
    attempt, token = start_assessment_attempt(owner, assessment.id, session=db.session)

    with pytest.raises(ForbiddenError, match="permission to manage this assessment attempt lease"):
        release_attempt_lease(
            actor=peer,
            attempt_id=attempt.id,
            raw_lease_token=token,
            session=db.session,
        )


def test_instructor_cannot_manipulate_student_lease(
    app: Flask,
    enrolled_students: tuple[User, User],
    instructor_user: User,
    published_course: Course,
) -> None:
    """Verify instructor managing the course cannot heartbeat, takeover, or release lease."""
    owner, _ = enrolled_students
    assessment = _make_assessment_with_question(instructor_user, published_course)
    attempt, token = start_assessment_attempt(owner, assessment.id, session=db.session)

    with pytest.raises(ForbiddenError):
        renew_attempt_lease(
            actor=instructor_user,
            attempt_id=attempt.id,
            raw_lease_token=token,
            session=db.session,
        )

    with pytest.raises(ForbiddenError):
        takeover_attempt_lease(
            actor=instructor_user,
            attempt_id=attempt.id,
            session=db.session,
        )

    with pytest.raises(ForbiddenError):
        release_attempt_lease(
            actor=instructor_user,
            attempt_id=attempt.id,
            raw_lease_token=token,
            session=db.session,
        )


def test_admin_cannot_manipulate_student_lease(
    app: Flask,
    enrolled_students: tuple[User, User],
    admin_user: User,
    instructor_user: User,
    published_course: Course,
) -> None:
    """Verify system administrator cannot manipulate student active editing lease."""
    owner, _ = enrolled_students
    assessment = _make_assessment_with_question(instructor_user, published_course)
    attempt, token = start_assessment_attempt(owner, assessment.id, session=db.session)

    with pytest.raises(ForbiddenError):
        renew_attempt_lease(
            actor=admin_user,
            attempt_id=attempt.id,
            raw_lease_token=token,
            session=db.session,
        )

    with pytest.raises(ForbiddenError):
        takeover_attempt_lease(
            actor=admin_user,
            attempt_id=attempt.id,
            session=db.session,
        )


def test_token_masking_storage_and_serialization(
    app: Flask,
    enrolled_students: tuple[User, User],
    instructor_user: User,
    published_course: Course,
) -> None:
    """Verify raw token is never stored in DB and never exposed in serialized attempt dictionary."""
    owner, _ = enrolled_students
    assessment = _make_assessment_with_question(instructor_user, published_course)
    attempt, raw_token = start_assessment_attempt(owner, assessment.id, session=db.session)

    # 1. Database holds only 32-byte binary SHA-256 hash
    assert attempt.lease_token_hash is not None
    assert isinstance(attempt.lease_token_hash, bytes)
    assert len(attempt.lease_token_hash) == 32
    assert attempt.lease_token_hash == hashlib.sha256(raw_token.encode("utf-8")).digest()
    assert raw_token not in str(attempt.lease_token_hash)

    # 2. Serialized attempt dict contains no raw token or hash
    serialized = _serialize_attempt(attempt)
    assert "raw_token" not in serialized
    assert "lease_token" not in serialized
    assert "lease_token_hash" not in serialized
    assert "id" not in serialized  # ADR-002 compliance
