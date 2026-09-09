"""Unit tests for Attempt Lease Management & Multi-Tab Takeover Service (TASK-014).

Validates:
- Single active editing lease enforcement (Algorithm 07, ADR-005).
- Heartbeat renewal, expiry calculation, and deadline clamping (Algorithm 06).
- Takeover invalidation of previous lease token and generation of fresh token.
- Voluntary release of editing lease for clean tab close.
- Attempt deadline auto-expiration transitions (AttemptExpiredError).
- Lease token verification helper logic.
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
from pwd301.models.attempt_regrade import AssessmentAttempt
from pwd301.models.course import Course
from pwd301.models.identity import Role, User
from pwd301.models.notification_audit import AuditEvent
from pwd301.services.assessment_service import (
    _normalize_dt,
    assign_question,
    create_assessment,
    create_section,
    publish_assessment,
)
from pwd301.services.attempt_service import (
    release_attempt_lease,
    renew_attempt_lease,
    start_assessment_attempt,
    takeover_attempt_lease,
    verify_attempt_lease,
)
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.exceptions import (
    AttemptExpiredError,
    AttemptLeaseConflictError,
    AttemptLeaseExpiredError,
    AttemptValidationError,
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
    u = register_user("admin_lease_u@example.com", "Password@123", "Admin User")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create instructor user."""
    u = register_user("inst_lease_u@example.com", "Password@123", "Attempt Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create student user."""
    u = register_user("student_lease_u@example.com", "Password@123", "Attempt Student")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def published_course(app: Flask, instructor_user: User, admin_user: User) -> Course:
    """Create and publish a course owned by instructor."""
    c = create_course(
        instructor_user,
        {
            "course_code": "LEASE-101",
            "title": "Lease Testing Course",
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
        "title": "Lease Test Assessment",
        "assessment_type": "QUIZ",
        "time_limit_minutes": time_limit,
        "open_at": (now + timedelta(hours=open_delta_hours)).isoformat(),
        "close_at": (now + timedelta(hours=close_delta_hours)).isoformat(),
        "passing_score": 50.0,
    }
    assessment = create_assessment(instructor, course.id, payload, session=db.session)
    section = create_section(
        instructor, assessment.id, {"title": "Main Section"}, session=db.session
    )

    q_payload: dict[str, Any] = {
        "question_type": "SINGLE_CHOICE",
        "difficulty": "REMEMBER",
        "content": "What is lease duration?",
        "default_points": 10.0,
        "choices": [
            {"content": "30 seconds", "is_correct": True, "position": 1},
            {"content": "10 seconds", "is_correct": False, "position": 2},
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


def test_heartbeat_renews_lease_successfully(
    app: Flask,
    enrolled_student: User,
    instructor_user: User,
    published_course: Course,
) -> None:
    """Verify heartbeat extends lease_expires_at by 30 seconds and updates last_heartbeat_at."""
    assessment = _make_assessment_with_question(instructor_user, published_course)
    attempt, token = start_assessment_attempt(enrolled_student, assessment.id, session=db.session)

    initial_expires_at = attempt.lease_expires_at
    assert initial_expires_at is not None

    result = renew_attempt_lease(
        actor=enrolled_student,
        attempt_id=attempt.id,
        raw_lease_token=token,
        session=db.session,
    )

    assert result["attempt_id"] == str(attempt.public_id)
    assert result["status"] == "IN_PROGRESS"
    assert "lease_expires_at" in result
    assert "server_time" in result
    assert result["remaining_seconds"] is not None
    assert result["remaining_seconds"] > 0

    renewed_attempt = db.session.get(AssessmentAttempt, attempt.id)
    assert renewed_attempt is not None
    assert renewed_attempt.last_heartbeat_at is not None
    assert renewed_attempt.lease_expires_at is not None
    assert renewed_attempt.lease_expires_at >= initial_expires_at


def test_heartbeat_clamped_to_assessment_deadline(
    app: Flask,
    enrolled_student: User,
    instructor_user: User,
    published_course: Course,
) -> None:
    """Verify lease_expires_at is clamped to deadline_at when deadline is within 30 seconds."""
    assessment = _make_assessment_with_question(instructor_user, published_course)
    attempt, token = start_assessment_attempt(enrolled_student, assessment.id, session=db.session)

    # Set started_at in past and deadline 15 seconds from now
    now = datetime.now(UTC)
    attempt.started_at = now - timedelta(minutes=59)
    tight_deadline = now + timedelta(seconds=15)
    attempt.deadline_at = tight_deadline
    db.session.commit()

    result = renew_attempt_lease(
        actor=enrolled_student,
        attempt_id=attempt.id,
        raw_lease_token=token,
        session=db.session,
    )

    renewed_attempt = db.session.get(AssessmentAttempt, attempt.id)
    assert renewed_attempt is not None
    # Expiry must be clamped to the deadline, not now + 30s
    assert _normalize_dt(renewed_attempt.lease_expires_at) == _normalize_dt(tight_deadline)
    assert result["remaining_seconds"] <= 15


def test_heartbeat_wrong_token_raises_conflict(
    app: Flask,
    enrolled_student: User,
    instructor_user: User,
    published_course: Course,
) -> None:
    """Verify heartbeat with mismatched token raises AttemptLeaseConflictError (409)."""
    assessment = _make_assessment_with_question(instructor_user, published_course)
    attempt, _ = start_assessment_attempt(enrolled_student, assessment.id, session=db.session)

    stale_token = "0" * 64
    with pytest.raises(
        AttemptLeaseConflictError, match="Editing lease was lost or taken over by another window"
    ):
        renew_attempt_lease(
            actor=enrolled_student,
            attempt_id=attempt.id,
            raw_lease_token=stale_token,
            session=db.session,
        )


def test_heartbeat_expired_lease_raises_lease_expired_error(
    app: Flask,
    enrolled_student: User,
    instructor_user: User,
    published_course: Course,
) -> None:
    """Verify heartbeat called after lease has expired raises AttemptLeaseExpiredError (409)."""
    assessment = _make_assessment_with_question(instructor_user, published_course)
    attempt, token = start_assessment_attempt(enrolled_student, assessment.id, session=db.session)

    # Simulate lease expiry 5 seconds ago
    now = datetime.now(UTC)
    attempt.lease_expires_at = now - timedelta(seconds=5)
    db.session.commit()

    with pytest.raises(
        AttemptLeaseExpiredError, match="Editing lease was lost or taken over by another window"
    ):
        renew_attempt_lease(
            actor=enrolled_student,
            attempt_id=attempt.id,
            raw_lease_token=token,
            session=db.session,
        )


def test_heartbeat_past_deadline_transitions_to_expired(
    app: Flask,
    enrolled_student: User,
    instructor_user: User,
    published_course: Course,
) -> None:
    """Verify attempt past deadline_at auto-transitions to EXPIRED
    and raises AttemptExpiredError.
    """
    assessment = _make_assessment_with_question(instructor_user, published_course)
    attempt, token = start_assessment_attempt(enrolled_student, assessment.id, session=db.session)

    # Set started_at and deadline in the past while preserving started_at <= deadline_at
    now = datetime.now(UTC)
    attempt.started_at = now - timedelta(hours=2)
    attempt.deadline_at = now - timedelta(hours=1)
    db.session.commit()

    with pytest.raises(AttemptExpiredError, match="deadline has expired"):
        renew_attempt_lease(
            actor=enrolled_student,
            attempt_id=attempt.id,
            raw_lease_token=token,
            session=db.session,
        )

    # Database record must be committed as EXPIRED
    db.session.expire_all()
    updated = db.session.get(AssessmentAttempt, attempt.id)
    assert updated is not None
    assert updated.status == "EXPIRED"


def test_heartbeat_non_in_progress_attempt_raises_validation_error(
    app: Flask,
    enrolled_student: User,
    instructor_user: User,
    published_course: Course,
) -> None:
    """Verify heartbeat on non-IN_PROGRESS attempt raises AttemptValidationError."""
    assessment = _make_assessment_with_question(instructor_user, published_course)
    attempt, token = start_assessment_attempt(enrolled_student, assessment.id, session=db.session)

    attempt.status = "SUBMITTED"
    db.session.commit()

    with pytest.raises(AttemptValidationError, match="not in progress"):
        renew_attempt_lease(
            actor=enrolled_student,
            attempt_id=attempt.id,
            raw_lease_token=token,
            session=db.session,
        )


def test_takeover_generates_new_token_and_invalidates_previous(
    app: Flask,
    enrolled_student: User,
    instructor_user: User,
    published_course: Course,
) -> None:
    """Verify takeover issues a new token, hashes with SHA-256, and records audit event."""
    assessment = _make_assessment_with_question(instructor_user, published_course)
    attempt, initial_token = start_assessment_attempt(
        enrolled_student, assessment.id, session=db.session
    )

    taken_attempt, new_token = takeover_attempt_lease(
        actor=enrolled_student,
        attempt_id=attempt.id,
        session=db.session,
    )

    assert new_token != initial_token
    assert len(new_token) == 64  # 32-byte hex

    # Verify SHA-256 hash stored in DB
    expected_hash = hashlib.sha256(new_token.encode("utf-8")).digest()
    assert taken_attempt.lease_token_hash == expected_hash

    # Old token fails heartbeat immediately
    with pytest.raises(AttemptLeaseConflictError):
        renew_attempt_lease(
            actor=enrolled_student,
            attempt_id=attempt.id,
            raw_lease_token=initial_token,
            session=db.session,
        )

    # New token succeeds
    result = renew_attempt_lease(
        actor=enrolled_student,
        attempt_id=attempt.id,
        raw_lease_token=new_token,
        session=db.session,
    )
    assert result["status"] == "IN_PROGRESS"

    # Verify AuditEvent recorded
    audit = (
        db.session.query(AuditEvent)
        .filter(AuditEvent.target_id == attempt.id, AuditEvent.action == "LEASE_TAKEOVER")
        .first()
    )
    assert audit is not None
    assert audit.target_type == "ATTEMPT"


def test_takeover_clamped_to_deadline(
    app: Flask,
    enrolled_student: User,
    instructor_user: User,
    published_course: Course,
) -> None:
    """Verify takeover lease_expires_at is clamped to deadline."""
    assessment = _make_assessment_with_question(instructor_user, published_course)
    attempt, _ = start_assessment_attempt(enrolled_student, assessment.id, session=db.session)

    now = datetime.now(UTC)
    attempt.started_at = now - timedelta(minutes=59)
    tight_deadline = now + timedelta(seconds=20)
    attempt.deadline_at = tight_deadline
    db.session.commit()

    taken_attempt, _ = takeover_attempt_lease(
        actor=enrolled_student,
        attempt_id=attempt.id,
        session=db.session,
    )
    assert _normalize_dt(taken_attempt.lease_expires_at) == _normalize_dt(tight_deadline)


def test_takeover_past_deadline_transitions_to_expired(
    app: Flask,
    enrolled_student: User,
    instructor_user: User,
    published_course: Course,
) -> None:
    """Verify takeover past deadline auto-transitions to EXPIRED and raises AttemptExpiredError."""
    assessment = _make_assessment_with_question(instructor_user, published_course)
    attempt, _ = start_assessment_attempt(enrolled_student, assessment.id, session=db.session)

    now = datetime.now(UTC)
    attempt.started_at = now - timedelta(hours=2)
    attempt.deadline_at = now - timedelta(hours=1)
    db.session.commit()

    with pytest.raises(AttemptExpiredError, match="deadline has expired"):
        takeover_attempt_lease(
            actor=enrolled_student,
            attempt_id=attempt.id,
            session=db.session,
        )

    db.session.expire_all()
    updated = db.session.get(AssessmentAttempt, attempt.id)
    assert updated is not None
    assert updated.status == "EXPIRED"


def test_release_clears_lease_and_records_audit(
    app: Flask,
    enrolled_student: User,
    instructor_user: User,
    published_course: Course,
) -> None:
    """Verify voluntary release clears lease_token_hash and records LEASE_RELEASED audit."""
    assessment = _make_assessment_with_question(instructor_user, published_course)
    attempt, token = start_assessment_attempt(enrolled_student, assessment.id, session=db.session)

    release_attempt_lease(
        actor=enrolled_student,
        attempt_id=attempt.id,
        raw_lease_token=token,
        session=db.session,
    )

    db.session.expire_all()
    updated = db.session.get(AssessmentAttempt, attempt.id)
    assert updated is not None
    assert updated.lease_token_hash is None

    # Heartbeat with previous token now fails
    with pytest.raises(AttemptLeaseConflictError):
        renew_attempt_lease(
            actor=enrolled_student,
            attempt_id=attempt.id,
            raw_lease_token=token,
            session=db.session,
        )

    # Verify AuditEvent
    audit = (
        db.session.query(AuditEvent)
        .filter(AuditEvent.target_id == attempt.id, AuditEvent.action == "LEASE_RELEASED")
        .first()
    )
    assert audit is not None


def test_release_wrong_token_raises_conflict(
    app: Flask,
    enrolled_student: User,
    instructor_user: User,
    published_course: Course,
) -> None:
    """Verify release with wrong token raises AttemptLeaseConflictError."""
    assessment = _make_assessment_with_question(instructor_user, published_course)
    attempt, _ = start_assessment_attempt(enrolled_student, assessment.id, session=db.session)

    with pytest.raises(AttemptLeaseConflictError):
        release_attempt_lease(
            actor=enrolled_student,
            attempt_id=attempt.id,
            raw_lease_token="bad_token_123",
            session=db.session,
        )


def test_verify_attempt_lease_truth_table(
    app: Flask,
    enrolled_student: User,
    instructor_user: User,
    published_course: Course,
) -> None:
    """Verify truth table of verify_attempt_lease under all edge conditions."""
    assessment = _make_assessment_with_question(instructor_user, published_course)
    attempt, token = start_assessment_attempt(enrolled_student, assessment.id, session=db.session)

    # 1. Valid attempt, valid token -> True
    assert verify_attempt_lease(attempt, token) is True

    # 2. Invalid / wrong token -> False
    assert verify_attempt_lease(attempt, "wrong_token") is False
    assert verify_attempt_lease(attempt, "") is False
    assert verify_attempt_lease(attempt, None) is False

    # 3. Expired lease -> False
    now = datetime.now(UTC)
    attempt.lease_expires_at = now - timedelta(seconds=1)
    assert verify_attempt_lease(attempt, token) is False

    # Reset lease
    attempt.lease_expires_at = now + timedelta(seconds=30)
    assert verify_attempt_lease(attempt, token) is True

    # 4. Past deadline -> False
    attempt.deadline_at = now - timedelta(seconds=1)
    assert verify_attempt_lease(attempt, token) is False

    # Reset deadline
    attempt.deadline_at = now + timedelta(minutes=10)
    assert verify_attempt_lease(attempt, token) is True

    # 5. Non-IN_PROGRESS status -> False
    attempt.status = "SUBMITTED"
    assert verify_attempt_lease(attempt, token) is False

    # 6. Null lease_token_hash -> False
    attempt.status = "IN_PROGRESS"
    attempt.lease_token_hash = None
    assert verify_attempt_lease(attempt, token) is False
