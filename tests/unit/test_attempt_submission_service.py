"""Unit tests for Attempt Submission & Idempotency Engine (TASK-015).

Validates:
- Transition from IN_PROGRESS to SUBMITTED terminal state.
- Idempotent submission replay when called repeatedly with the same idempotency key.
- SubmissionIdempotencyConflictError when attempting to submit with a different key.
- Server-authoritative deadline enforcement transitioning overdue attempts to EXPIRED.
- Complete revocation of editing lease upon submission.
- Append-only audit logging (ATTEMPT_SUBMITTED).
- Validation of idempotency key UUID format.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from flask import Flask
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.assessment import Assessment
from pwd301.models.course import Course
from pwd301.models.identity import Role, User
from pwd301.models.notification_audit import AuditEvent
from pwd301.services.assessment_service import (
    assign_question,
    create_assessment,
    create_section,
    publish_assessment,
)
from pwd301.services.attempt_service import (
    start_assessment_attempt,
    submit_assessment_attempt,
)
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.exceptions import (
    AttemptExpiredError,
    AttemptValidationError,
    SubmissionIdempotencyConflictError,
)
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
    u = register_user("admin_sub_u@example.com", "Password@123", "Admin User")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create instructor user."""
    u = register_user("inst_sub_u@example.com", "Password@123", "Attempt Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create student user."""
    u = register_user("student_sub_u@example.com", "Password@123", "Attempt Student")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def published_course(app: Flask, instructor_user: User, admin_user: User) -> Course:
    """Create and publish a course owned by instructor."""
    c = create_course(
        instructor_user,
        {
            "course_code": "SUBMIT-101",
            "title": "Submission Testing Course",
            "summary": "Core Course",
        },
    )
    change_course_status(instructor_user, c.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin_user, c.id, "APPROVED")
    change_course_status(admin_user, c.id, "PUBLISHED")
    db.session.commit()
    return c


@pytest.fixture
def enrolled_student(app: Flask, student_user: User, published_course: Course) -> User:
    """Enroll student into the published course."""
    enroll_student(student_user, published_course.id, session=db.session)
    db.session.commit()
    return student_user


def _make_assessment_with_question(
    instructor: User,
    course: Course,
    time_limit: int | None = 60,
    open_delta_hours: int = -1,
    close_delta_hours: int = 24,
) -> Assessment:
    """Helper to create and publish an assessment with one assigned question."""
    now = datetime.now(UTC)
    payload = {
        "title": "Submission Test Assessment",
        "assessment_type": "QUIZ",
        "time_limit_minutes": time_limit,
        "open_at": (now + timedelta(hours=open_delta_hours)).isoformat(),
        "close_at": (now + timedelta(hours=close_delta_hours)).isoformat(),
        "passing_score": 50.0,
    }
    assessment = create_assessment(instructor, course.id, payload, session=db.session)
    sec = create_section(instructor, assessment.id, {"title": "Main Section"}, session=db.session)

    q_data: dict[str, Any] = {
        "question_type": "SINGLE_CHOICE",
        "difficulty": "REMEMBER",
        "content": "Which HTTP status represents Conflict?",
        "default_points": 10.0,
        "choices": [
            {"content": "409", "is_correct": True, "position": 1},
            {"content": "404", "is_correct": False, "position": 2},
        ],
    }
    q = create_question(instructor, course.id, q_data, session=db.session)
    assign_question(
        instructor,
        assessment.id,
        {"question_id": q.id, "points_assigned": 10.0, "section_id": sec.id},
        session=db.session,
    )

    publish_assessment(instructor, assessment.id, session=db.session)
    db.session.commit()
    return assessment


def test_submit_assessment_attempt_transition(
    app: Flask,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
) -> None:
    """Submitting attempt transitions status from IN_PROGRESS to SUBMITTED and revokes lease."""
    sess: Session = db.session
    assessment = _make_assessment_with_question(instructor_user, published_course)

    attempt, lease_token = start_assessment_attempt(enrolled_student, assessment.id, session=sess)
    assert attempt.status == "IN_PROGRESS"
    assert attempt.lease_token_hash is not None

    key = uuid.uuid4()
    result = submit_assessment_attempt(
        actor=enrolled_student,
        attempt_id=attempt.id,
        idempotency_key=key,
        raw_lease_token=lease_token,
        session=sess,
    )

    assert result["status"] == "SUBMITTED"
    assert result["is_idempotent_replay"] is False
    assert result["submission_idempotency_key"] == str(key)
    assert result["submitted_at"] is not None
    assert result["finalized_at"] is not None

    sess.refresh(attempt)
    assert attempt.status == "SUBMITTED"
    assert str(attempt.submission_idempotency_key) == str(key)
    assert attempt.lease_token_hash is None
    assert attempt.lease_expires_at is None

    # Verify append-only AuditEvent
    audit = (
        sess.query(AuditEvent)
        .filter(
            AuditEvent.target_type == "ATTEMPT",
            AuditEvent.target_id == attempt.id,
            AuditEvent.action == "ATTEMPT_SUBMITTED",
        )
        .first()
    )
    assert audit is not None
    assert audit.actor_user_id == enrolled_student.id


def test_submit_idempotent_replay(
    app: Flask,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
) -> None:
    """Repeated submissions with the same idempotency key return original result idempotently."""
    sess: Session = db.session
    assessment = _make_assessment_with_question(instructor_user, published_course)

    attempt, lease_token = start_assessment_attempt(enrolled_student, assessment.id, session=sess)

    key = uuid.uuid4()
    res1 = submit_assessment_attempt(
        actor=enrolled_student,
        attempt_id=attempt.id,
        idempotency_key=key,
        raw_lease_token=lease_token,
        session=sess,
    )
    assert res1["status"] == "SUBMITTED"
    assert res1["is_idempotent_replay"] is False

    # Second call with the same idempotency key
    res2 = submit_assessment_attempt(
        actor=enrolled_student,
        attempt_id=attempt.id,
        idempotency_key=key,
        session=sess,
    )
    assert res2["status"] == "SUBMITTED"
    assert res2["is_idempotent_replay"] is True
    assert res2["submission_idempotency_key"] == str(key)
    assert res2["submitted_at"] == res1["submitted_at"]


def test_submit_conflict_with_different_idempotency_key(
    app: Flask,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
) -> None:
    """Submitting with a different idempotency key raises conflict error."""
    sess: Session = db.session
    assessment = _make_assessment_with_question(instructor_user, published_course)

    attempt, lease_token = start_assessment_attempt(enrolled_student, assessment.id, session=sess)

    key1 = uuid.uuid4()
    submit_assessment_attempt(
        actor=enrolled_student,
        attempt_id=attempt.id,
        idempotency_key=key1,
        raw_lease_token=lease_token,
        session=sess,
    )

    key2 = uuid.uuid4()
    with pytest.raises(SubmissionIdempotencyConflictError):
        submit_assessment_attempt(
            actor=enrolled_student,
            attempt_id=attempt.id,
            idempotency_key=key2,
            session=sess,
        )


def test_submit_rejected_after_deadline_expired(
    app: Flask,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
) -> None:
    """Submitting after attempt deadline transitions attempt to EXPIRED and raises error."""
    sess: Session = db.session
    assessment = _make_assessment_with_question(instructor_user, published_course)

    attempt, lease_token = start_assessment_attempt(enrolled_student, assessment.id, session=sess)
    attempt.started_at = datetime.now(UTC) - timedelta(hours=2)
    attempt.deadline_at = datetime.now(UTC) - timedelta(minutes=5)
    sess.commit()

    with pytest.raises(AttemptExpiredError):
        submit_assessment_attempt(
            actor=enrolled_student,
            attempt_id=attempt.id,
            idempotency_key=uuid.uuid4(),
            raw_lease_token=lease_token,
            session=sess,
        )

    sess.refresh(attempt)
    assert attempt.status == "EXPIRED"


def test_submit_invalid_idempotency_key_format(
    app: Flask,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
) -> None:
    """Providing a malformed idempotency key raises AttemptValidationError."""
    sess: Session = db.session
    assessment = _make_assessment_with_question(instructor_user, published_course)

    attempt, lease_token = start_assessment_attempt(enrolled_student, assessment.id, session=sess)

    with pytest.raises(AttemptValidationError) as exc_info:
        submit_assessment_attempt(
            actor=enrolled_student,
            attempt_id=attempt.id,
            idempotency_key="not-a-valid-uuid",
            raw_lease_token=lease_token,
            session=sess,
        )
    assert "Invalid submission idempotency key format" in str(exc_info.value)
