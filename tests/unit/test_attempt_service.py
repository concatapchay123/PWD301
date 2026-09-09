"""Unit tests for Student Assessment Delivery, Attempt Snapshot & Server Timer (TASK-013)."""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from flask import Flask
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.assessment import Assessment
from pwd301.models.course import Course
from pwd301.models.identity import Role, User
from pwd301.models.notification_audit import AuditEvent
from pwd301.models.question_bank import Question
from pwd301.services.assessment_service import (
    assign_question,
    create_assessment,
    create_section,
    publish_assessment,
)
from pwd301.services.attempt_service import (
    _calculate_deadline,
    get_attempt_delivery,
    list_student_assessment_attempts,
    start_assessment_attempt,
)
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import enroll_student, leave_course
from pwd301.services.exceptions import (
    ActiveAttemptExistsError,
    AssessmentClosedError,
    AssessmentNotOpenError,
    AttemptLimitExceededError,
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
    u = register_user("admin_attempt@example.com", "Password@123", "Admin User")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create instructor user."""
    u = register_user("inst_attempt@example.com", "Password@123", "Attempt Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create student user."""
    u = register_user("student_attempt@example.com", "Password@123", "Attempt Student")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def published_course(app: Flask, instructor_user: User, admin_user: User) -> Course:
    """Create and publish a course owned by instructor."""
    c = create_course(
        instructor_user,
        {
            "course_code": "CS-201",
            "title": "Data Structures & Algorithms",
            "summary": "Core CS",
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


def _make_mcq_question(
    instructor: User,
    course: Course,
    content: str = "Sample question?",
    fixed_choice_content: str | None = None,
) -> Question:
    """Helper to create a single choice question with choices."""
    choices_data = [
        {"content": "Option Alpha", "is_correct": True, "position": 1},
        {"content": "Option Beta", "is_correct": False, "position": 2},
        {"content": "Option Gamma", "is_correct": False, "position": 3},
    ]
    if fixed_choice_content:
        choices_data.append(
            {
                "content": fixed_choice_content,
                "is_correct": False,
                "position": 4,
                "is_fixed_position": True,
            }
        )
    payload = {
        "question_type": "SINGLE_CHOICE",
        "difficulty": "REMEMBER",
        "content": content,
        "explanation": "This is a secret explanation that must never leak.",
        "default_points": 5.0,
        "choices": choices_data,
        "provenance": {"source_type": "MANUAL", "notes": "Test question"},
    }
    q = create_question(instructor, course.id, payload, session=db.session)
    db.session.commit()
    return q


_UNSET: Any = object()


def _create_published_assessment(
    instructor: User,
    course: Course,
    time_limit_minutes: int | None = 60,
    attempt_limit: int | None = 3,
    shuffle_questions: bool = False,
    shuffle_choices: bool = False,
    open_at: datetime | None = None,
    close_at: Any = _UNSET,
) -> tuple[Assessment, list[Question]]:
    """Helper to create and publish a valid assessment with questions."""
    now = datetime.now(UTC)
    if open_at is None:
        open_at = now - timedelta(hours=1)
    if close_at is _UNSET:
        close_at = now + timedelta(days=2)

    payload = {
        "title": "Algorithms Midterm Exam",
        "description": "Comprehensive midterm",
        "assessment_type": "MIDTERM",
        "scoring_policy": "HIGHEST",
        "score_release_policy": "AFTER_CLOSE",
        "time_limit_minutes": time_limit_minutes,
        "attempt_limit": attempt_limit,
        "passing_percent": 60.0,
        "shuffle_questions": shuffle_questions,
        "shuffle_choices": shuffle_choices,
        "open_at": open_at.isoformat() if open_at else None,
        "close_at": close_at.isoformat() if close_at else None,
    }
    assessment = create_assessment(instructor, course.id, payload, session=db.session)

    sec = create_section(
        instructor,
        assessment.public_id,
        {"title": "Section 1: Basics", "position": 1},
        session=db.session,
    )

    q1 = _make_mcq_question(instructor, course, content="What is O(1)?")
    q2 = _make_mcq_question(
        instructor,
        course,
        content="Which is a linear structure?",
        fixed_choice_content="None of the above",
    )

    assign_question(
        instructor,
        assessment.public_id,
        {"question_id": str(q1.public_id), "section_id": sec.id, "points": 5.0},
        session=db.session,
    )
    assign_question(
        instructor,
        assessment.public_id,
        {"question_id": str(q2.public_id), "section_id": sec.id, "points": 10.0},
        session=db.session,
    )

    publish_assessment(instructor, assessment.public_id, session=db.session)
    db.session.commit()
    return assessment, [q1, q2]


# ============================================================================
# UNIT TESTS
# ============================================================================


def test_start_attempt_success(
    app: Flask,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
) -> None:
    """Test standard attempt start with presentation snapshots, timer, and lease."""
    assessment, questions = _create_published_assessment(instructor_user, published_course)

    attempt, raw_token = start_assessment_attempt(
        student_actor=enrolled_student,
        assessment_id=assessment.public_id,
        session=db.session,
    )
    db.session.commit()

    assert attempt.id is not None
    assert attempt.public_id is not None
    assert attempt.status == "IN_PROGRESS"
    assert attempt.attempt_number == 1
    assert attempt.student_user_id == enrolled_student.id
    assert attempt.started_at is not None
    assert attempt.deadline_at is not None

    # Verify questions snapshot
    assert len(attempt.attempt_questions) == 2
    aq1 = attempt.attempt_questions[0]
    assert aq1.position == 1
    assert aq1.question_type_snapshot == "SINGLE_CHOICE"
    assert aq1.content_snapshot == "What is O(1)?"
    assert aq1.points_assigned == Decimal("5.0000")

    # Verify choices snapshot (no is_correct in snapshot)
    assert len(aq1.choice_snapshots) == 3
    for cs in aq1.choice_snapshots:
        assert isinstance(cs.choice_key_snapshot, uuid.UUID)
        assert cs.content_snapshot in ["Option Alpha", "Option Beta", "Option Gamma"]
        assert not hasattr(cs, "is_correct")

    # Verify question revision exposure and usage count
    q1 = questions[0]
    rev = q1.current_revision
    assert rev is not None
    assert rev.was_student_exposed is True
    assert q1.usage_count >= 1
    assert q1.first_used_at is not None

    # Verify audit event
    audit = (
        db.session.query(AuditEvent)
        .filter(AuditEvent.target_type == "ATTEMPT", AuditEvent.target_id == attempt.id)
        .first()
    )
    assert audit is not None
    assert audit.action == "ATTEMPT_STARTED"
    assert audit.actor_user_id == enrolled_student.id

    # Test delivery presentation contract
    delivery = get_attempt_delivery(enrolled_student, attempt.public_id, session=db.session)
    assert delivery["attempt_id"] == str(attempt.public_id)
    assert delivery["status"] == "IN_PROGRESS"
    assert delivery["total_questions"] == 2
    assert delivery["total_points"] == 15.0
    assert delivery["remaining_seconds"] is not None
    assert delivery["remaining_seconds"] > 0

    # Ensure delivery payload hides is_correct and explanation
    for q_data in delivery["questions"]:
        assert "explanation" not in q_data
        assert "source_question_id" not in q_data
        for c_data in q_data["choices"]:
            assert "is_correct" not in c_data
            assert "source_choice_id" not in c_data


def test_start_attempt_enforces_active_enrollment(
    app: Flask,
    instructor_user: User,
    student_user: User,
    published_course: Course,
    setup_roles: dict[str, Role],
) -> None:
    """Attempt start must reject students who have not enrolled or have left."""
    assessment, _ = _create_published_assessment(instructor_user, published_course)

    # 1. Not enrolled at all
    with pytest.raises(AttemptValidationError, match="does not have an active enrollment"):
        start_assessment_attempt(student_user, assessment.public_id, session=db.session)

    # 2. Enrolled then LEFT
    enroll_student(student_user, published_course.id, session=db.session)
    leave_course(student_user, published_course.id, session=db.session)
    db.session.commit()

    with pytest.raises(AttemptValidationError, match="does not have an active enrollment"):
        start_assessment_attempt(student_user, assessment.public_id, session=db.session)


def test_start_attempt_window_validation(
    app: Flask,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
) -> None:
    """Validate window enforcement: not open yet or already closed."""
    now = datetime.now(UTC)

    # Future open_at
    future_assessment, _ = _create_published_assessment(
        instructor_user,
        published_course,
        open_at=now + timedelta(days=1),
        close_at=now + timedelta(days=2),
    )
    with pytest.raises(AssessmentNotOpenError, match="not yet open"):
        start_assessment_attempt(enrolled_student, future_assessment.public_id, session=db.session)

    # Past close_at
    past_assessment, _ = _create_published_assessment(
        instructor_user,
        published_course,
        open_at=now - timedelta(days=2),
        close_at=now - timedelta(hours=1),
    )
    with pytest.raises(AssessmentClosedError, match="is closed"):
        start_assessment_attempt(enrolled_student, past_assessment.public_id, session=db.session)


def test_start_attempt_limit_exceeded(
    app: Flask,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
) -> None:
    """Enforce attempt limit when student exhausts allowed attempts."""
    assessment, _ = _create_published_assessment(instructor_user, published_course, attempt_limit=1)

    # First attempt starts successfully
    att1, _ = start_assessment_attempt(enrolled_student, assessment.public_id, session=db.session)
    db.session.commit()

    # Second attempt while first is in progress triggers active conflict
    with pytest.raises(ActiveAttemptExistsError, match="already in progress"):
        start_assessment_attempt(enrolled_student, assessment.public_id, session=db.session)

    # Finalize first attempt (status != IN_PROGRESS)
    att1.status = "SUBMITTED"
    db.session.commit()

    # Now attempt limit should be triggered
    with pytest.raises(AttemptLimitExceededError, match="limit .* reached"):
        start_assessment_attempt(enrolled_student, assessment.public_id, session=db.session)


def test_algorithm_06_deadline_calculation(
    app: Flask,
    instructor_user: User,
    published_course: Course,
) -> None:
    """Verify Algorithm 06: min(start + time_limit, close_at)."""
    now = datetime.now(UTC)

    # Case A: Nominal time limit < close_at
    assessment_a, _ = _create_published_assessment(
        instructor_user,
        published_course,
        time_limit_minutes=30,
        close_at=now + timedelta(hours=2),
    )
    deadline_a = _calculate_deadline(assessment_a, now)
    assert deadline_a is not None
    assert abs((deadline_a - (now + timedelta(minutes=30))).total_seconds()) < 1.0

    # Case B: Close_at is sooner than time_limit (student starts late)
    assessment_b, _ = _create_published_assessment(
        instructor_user,
        published_course,
        time_limit_minutes=60,
        close_at=now + timedelta(minutes=15),
    )
    deadline_b = _calculate_deadline(assessment_b, now)
    assert deadline_b is not None
    assert abs((deadline_b - (now + timedelta(minutes=15))).total_seconds()) < 1.0

    # Case C: Untimed assessment with close_at
    assessment_c, _ = _create_published_assessment(
        instructor_user,
        published_course,
        time_limit_minutes=None,
        close_at=now + timedelta(hours=5),
    )
    deadline_c = _calculate_deadline(assessment_c, now)
    assert deadline_c is not None
    assert abs((deadline_c - (now + timedelta(hours=5))).total_seconds()) < 1.0

    # Case D: Untimed assessment without close_at (e.g. practice)
    assessment_d, _ = _create_published_assessment(
        instructor_user,
        published_course,
        time_limit_minutes=None,
        close_at=None,
    )
    deadline_d = _calculate_deadline(assessment_d, now)
    assert deadline_d is None


def test_structural_freeze_triggered(
    app: Flask,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
) -> None:
    """Verify assessment.first_attempt_started_at is set immediately on attempt start."""
    assessment, _ = _create_published_assessment(instructor_user, published_course)
    assert assessment.first_attempt_started_at is None

    attempt, _ = start_assessment_attempt(
        enrolled_student, assessment.public_id, session=db.session
    )
    db.session.commit()

    db.session.refresh(assessment)
    assert assessment.first_attempt_started_at is not None
    first_started = assessment.first_attempt_started_at

    # Second attempt must not alter the freeze timestamp
    attempt.status = "SUBMITTED"
    db.session.commit()

    attempt2, _ = start_assessment_attempt(
        enrolled_student, assessment.public_id, session=db.session
    )
    db.session.commit()

    db.session.refresh(assessment)
    assert assessment.first_attempt_started_at == first_started


def test_shuffle_invariants(
    app: Flask,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
) -> None:
    """Verify shuffle_questions and shuffle_choices respecting is_fixed_position."""
    assessment, _ = _create_published_assessment(
        instructor_user,
        published_course,
        shuffle_questions=True,
        shuffle_choices=True,
    )

    attempt, _ = start_assessment_attempt(
        enrolled_student, assessment.public_id, session=db.session
    )
    db.session.commit()

    # All positions must be 1..N
    positions = [aq.position for aq in attempt.attempt_questions]
    assert sorted(positions) == [1, 2]

    # Inspect question with fixed choice ("None of the above")
    aq_with_fixed = next(
        aq for aq in attempt.attempt_questions if "linear" in aq.content_snapshot.lower()
    )
    assert aq_with_fixed.choice_shuffle_applied is True

    # The 4th choice was is_fixed_position=True ("None of the above")
    choices = sorted(aq_with_fixed.choice_snapshots, key=lambda c: c.position)
    assert len(choices) == 4
    assert choices[3].content_snapshot == "None of the above"
    assert choices[3].position == 4


def test_lease_token_generated(
    app: Flask,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
) -> None:
    """Verify cryptographically secure lease token generation and SHA-256 storage."""
    assessment, _ = _create_published_assessment(instructor_user, published_course)

    attempt, raw_token = start_assessment_attempt(
        enrolled_student, assessment.public_id, session=db.session
    )
    db.session.commit()

    assert isinstance(raw_token, str)
    assert len(raw_token) == 64  # 32 bytes in hex

    expected_hash = hashlib.sha256(raw_token.encode("utf-8")).digest()
    assert attempt.lease_token_hash == expected_hash
    assert attempt.lease_acquired_at is not None
    assert attempt.lease_expires_at is not None
    assert attempt.lease_expires_at > attempt.lease_acquired_at


def test_active_attempt_conflict(
    app: Flask,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
) -> None:
    """Starting an attempt while another is IN_PROGRESS raises ActiveAttemptExistsError."""
    assessment, _ = _create_published_assessment(instructor_user, published_course)

    start_assessment_attempt(enrolled_student, assessment.public_id, session=db.session)
    db.session.commit()

    with pytest.raises(ActiveAttemptExistsError, match="already in progress"):
        start_assessment_attempt(enrolled_student, assessment.public_id, session=db.session)


def test_expired_attempt_auto_transitions(
    app: Flask,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
) -> None:
    """An attempt past its deadline is automatically transitioned to EXPIRED."""
    assessment, _ = _create_published_assessment(instructor_user, published_course)

    att1, _ = start_assessment_attempt(enrolled_student, assessment.public_id, session=db.session)
    # Force started_at and deadline_at into the past while preserving deadline_at >= started_at
    att1.started_at = datetime.now(UTC) - timedelta(hours=2)
    att1.deadline_at = datetime.now(UTC) - timedelta(hours=1)
    db.session.commit()

    # Now starting a second attempt should transition att1 to EXPIRED and succeed
    att2, _ = start_assessment_attempt(enrolled_student, assessment.public_id, session=db.session)
    db.session.commit()

    db.session.refresh(att1)
    assert att1.status == "EXPIRED"
    assert att2.status == "IN_PROGRESS"
    assert att2.attempt_number == 2


def test_list_student_assessment_attempts(
    app: Flask,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
) -> None:
    """Verify list_student_assessment_attempts returns formatted history."""
    assessment, _ = _create_published_assessment(instructor_user, published_course)

    att1, _ = start_assessment_attempt(enrolled_student, assessment.public_id, session=db.session)
    att1.status = "SUBMITTED"
    db.session.commit()

    att2, _ = start_assessment_attempt(enrolled_student, assessment.public_id, session=db.session)
    db.session.commit()

    attempts = list_student_assessment_attempts(
        enrolled_student, assessment.public_id, session=db.session
    )
    assert len(attempts) == 2
    assert attempts[0]["attempt_number"] == 1
    assert attempts[0]["status"] == "SUBMITTED"
    assert attempts[1]["attempt_number"] == 2
    assert attempts[1]["status"] == "IN_PROGRESS"


def test_active_attempt_unique_index_concurrency(
    app: Flask,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify that DB unique index ux_attempt_single_active catches race condition."""
    from pwd301.models.attempt_regrade import AssessmentAttempt

    assessment, _ = _create_published_assessment(instructor_user, published_course)

    # First attempt starts normally
    start_assessment_attempt(enrolled_student, assessment.public_id, session=db.session)
    db.session.commit()

    # Simulate race condition where application-level select check is bypassed
    original_query = db.session.query

    def mocked_query(*args: Any, **kwargs: Any) -> Any:
        q = original_query(*args, **kwargs)
        if len(args) == 1 and args[0] is AssessmentAttempt:
            return q.filter(db.text("1=0"))
        return q

    monkeypatch.setattr(db.session, "query", mocked_query)

    # Even though app-level select check was bypassed, the DB unique index
    # blocks duplicate active attempt
    with pytest.raises(ActiveAttemptExistsError, match="already in progress"):
        start_assessment_attempt(enrolled_student, assessment.public_id, session=db.session)
