"""Unit tests for Assessment Builder & Engine (TASK-012)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from flask import Flask
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course, Lesson
from pwd301.models.identity import Role, User
from pwd301.models.notification_audit import AuditEvent
from pwd301.models.question_bank import Question
from pwd301.services.assessment_service import (
    _serialize_assessment,
    assign_question,
    cancel_assessment,
    configure_blueprint,
    create_assessment,
    create_section,
    delete_section,
    get_assessment_detail,
    materialize_blueprint_pool,
    publish_assessment,
    remove_question_assignment,
    restore_assessment,
    trash_assessment,
    update_assessment,
)
from pwd301.services.course_service import create_course
from pwd301.services.exceptions import (
    AssessmentLockedError,
    AssessmentValidationError,
    BlueprintValidationError,
)
from pwd301.services.lesson_service import create_lesson
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
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create primary instructor user."""
    u = register_user("inst_assess@example.com", "Password@123", "Assessment Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def course(app: Flask, instructor_user: User) -> Course:
    """Create a course owned by instructor."""
    c = create_course(
        instructor_user,
        {
            "course_code": "CS-101",
            "title": "Intro to CS",
            "summary": "Computer Science Fundamentals",
            "description": "Comprehensive course",
        },
    )
    db.session.commit()
    return c


@pytest.fixture
def lesson(app: Flask, instructor_user: User, course: Course) -> Lesson:
    """Create a lesson in the course."""
    les = create_lesson(
        instructor_user,
        course.id,
        {
            "title": "Lesson 1: Basics",
            "position": 1,
        },
    )
    db.session.commit()
    return les


def _make_approved_question(
    instructor: User,
    course: Course,
    content: str = "What is Python?",
    difficulty: str = "REMEMBER",
    question_type: str = "SINGLE_CHOICE",
) -> Question:
    """Helper to create a question with valid status and choices."""
    payload = {
        "question_type": question_type,
        "difficulty": difficulty,
        "content": content,
        "learning_objective": "Fundamentals",
        "default_points": 2.0,
        "choices": [
            {"content": "Programming language", "is_correct": True, "position": 1},
            {"content": "A reptile only", "is_correct": False, "position": 2},
        ],
        "provenance": {"source_type": "MANUAL", "notes": "Test question"},
    }
    q = create_question(instructor, course.id, payload, session=db.session)
    db.session.commit()
    return q


def test_create_assessment_success(app: Flask, course: Course, instructor_user: User) -> None:
    """Test standard assessment creation with default draft state."""
    now = datetime.now(UTC)
    open_at = now + timedelta(days=1)
    close_at = now + timedelta(days=2)

    payload = {
        "title": "Midterm Exam 1",
        "description": "First midterm exam",
        "assessment_type": "MIDTERM",
        "scoring_policy": "HIGHEST",
        "score_release_policy": "AFTER_CLOSE",
        "time_limit_minutes": 60,
        "attempt_limit": 2,
        "passing_percent": 70.0,
        "open_at": open_at.isoformat(),
        "close_at": close_at.isoformat(),
    }

    assessment = create_assessment(instructor_user, course.id, payload)
    db.session.commit()

    assert assessment.id is not None
    assert assessment.public_id is not None
    assert assessment.title == "Midterm Exam 1"
    assert assessment.status == "DRAFT"
    assert assessment.assessment_type == "MIDTERM"
    assert assessment.scoring_policy == "HIGHEST"
    assert assessment.score_release_policy == "AFTER_CLOSE"
    assert assessment.time_limit_minutes == 60
    assert assessment.attempt_limit == 2
    assert assessment.passing_percent == Decimal("70.0")

    # Audit event should be recorded
    audit = (
        db.session.query(AuditEvent)
        .filter(AuditEvent.target_id == assessment.id, AuditEvent.action == "ASSESSMENT_CREATED")
        .first()
    )
    assert audit is not None
    assert audit.actor_user_id == instructor_user.id


def test_create_assessment_validation_failures(
    app: Flask, course: Course, instructor_user: User
) -> None:
    """Test assessment creation rejects invalid parameters."""
    # Blank title
    with pytest.raises(AssessmentValidationError, match="title is required"):
        create_assessment(instructor_user, course.id, {"title": "  "})

    # Invalid type
    with pytest.raises(AssessmentValidationError, match="Invalid assessment_type"):
        create_assessment(
            instructor_user,
            course.id,
            {"title": "Exam", "assessment_type": "INVALID_TYPE"},
        )

    # Negative time limit
    with pytest.raises(
        AssessmentValidationError, match="time_limit_minutes must be greater than 0"
    ):
        create_assessment(
            instructor_user,
            course.id,
            {"title": "Exam", "assessment_type": "QUIZ", "time_limit_minutes": -5},
        )

    # Non-positive attempt limit
    with pytest.raises(AssessmentValidationError, match="attempt_limit must be greater than 0"):
        create_assessment(
            instructor_user,
            course.id,
            {"title": "Exam", "assessment_type": "QUIZ", "attempt_limit": 0},
        )

    # Passing percent out of range
    with pytest.raises(
        AssessmentValidationError, match="passing_percent must be between 0 and 100"
    ):
        create_assessment(
            instructor_user,
            course.id,
            {"title": "Exam", "assessment_type": "QUIZ", "passing_percent": -10},
        )

    # Invalid open/close timing (open >= close)
    now = datetime.now(UTC)
    with pytest.raises(
        AssessmentValidationError, match="open_at must be strictly earlier than close_at"
    ):
        create_assessment(
            instructor_user,
            course.id,
            {
                "title": "Exam",
                "assessment_type": "QUIZ",
                "open_at": (now + timedelta(days=2)).isoformat(),
                "close_at": (now + timedelta(days=1)).isoformat(),
            },
        )


def test_update_assessment_draft(app: Flask, course: Course, instructor_user: User) -> None:
    """Test modifying draft assessment settings."""
    assessment = create_assessment(
        instructor_user,
        course.id,
        {"title": "Quiz 1", "assessment_type": "QUIZ"},
    )
    db.session.commit()

    updated = update_assessment(
        instructor_user,
        assessment.public_id,
        {"title": "Updated Quiz 1", "time_limit_minutes": 30, "attempt_limit": 3},
    )
    db.session.commit()

    assert updated.title == "Updated Quiz 1"
    assert updated.time_limit_minutes == 30
    assert updated.attempt_limit == 3


def test_sections_crud_and_reorder(app: Flask, course: Course, instructor_user: User) -> None:
    """Test managing sections in an assessment."""
    assessment = create_assessment(
        instructor_user,
        course.id,
        {"title": "Final Exam", "assessment_type": "FINAL"},
    )
    db.session.commit()

    # Add sections
    sec1 = create_section(
        instructor_user,
        assessment.public_id,
        {
            "title": "Section A: Multiple Choice",
            "position": 1,
            "instructions": "Choose best answer",
        },
    )
    sec2 = create_section(
        instructor_user,
        assessment.public_id,
        {"title": "Section B: Coding", "position": 2},
    )
    db.session.commit()

    assert sec1.id is not None
    assert sec2.id is not None

    detail = get_assessment_detail(instructor_user, assessment.public_id)
    assert len(detail["sections"]) == 2
    assert detail["sections"][0]["title"] == "Section A: Multiple Choice"
    assert detail["sections"][1]["title"] == "Section B: Coding"

    # Delete section
    deleted = delete_section(instructor_user, assessment.public_id, sec2.id)
    db.session.commit()
    assert deleted is True

    detail2 = get_assessment_detail(instructor_user, assessment.public_id)
    assert len(detail2["sections"]) == 1
    assert detail2["sections"][0]["title"] == "Section A: Multiple Choice"


def test_fixed_question_assignment_and_removal(
    app: Flask, course: Course, instructor_user: User
) -> None:
    """Test fixed question assignment, points calculation, and removal."""
    assessment = create_assessment(
        instructor_user,
        course.id,
        {"title": "Quiz 2", "assessment_type": "QUIZ"},
    )
    sec = create_section(
        instructor_user,
        assessment.public_id,
        {"title": "General Knowledge", "position": 1},
    )
    db.session.commit()

    q1 = _make_approved_question(instructor_user, course, content="Question 1")
    q2 = _make_approved_question(instructor_user, course, content="Question 2")

    # Assign Q1 with 2.5 points
    a1 = assign_question(
        instructor_user,
        assessment.public_id,
        {
            "question_id": str(q1.public_id),
            "section_id": sec.id,
            "points": 2.5,
            "position": 1,
        },
    )
    db.session.commit()
    assert a1.points == Decimal("2.5")

    # Assign Q2 with 3.5 points
    a2 = assign_question(
        instructor_user,
        assessment.public_id,
        {
            "question_id": str(q2.public_id),
            "section_id": sec.id,
            "points": 3.5,
            "position": 2,
        },
    )
    db.session.commit()
    assert a2.points == Decimal("3.5")

    # Duplicate assignment rejection
    with pytest.raises(AssessmentValidationError, match="already assigned"):
        assign_question(
            instructor_user,
            assessment.public_id,
            {"question_id": str(q1.public_id), "section_id": sec.id},
        )

    # Check serialized aggregates
    serialized = _serialize_assessment(assessment, full=True)
    assert serialized["total_points"] == 6.0
    assert serialized["questions_count"] == 2

    # Remove Q1
    removed = remove_question_assignment(instructor_user, assessment.public_id, q1.id)
    db.session.commit()
    assert removed is True

    serialized_after = _serialize_assessment(assessment, full=True)
    assert serialized_after["total_points"] == 3.5
    assert serialized_after["questions_count"] == 1


def test_cross_course_question_assignment_rejected(
    app: Flask, course: Course, instructor_user: User
) -> None:
    """Cross-course defense: cannot assign question from Course B to Course A assessment."""
    other_course = create_course(
        instructor_user,
        {
            "course_code": "CS-202",
            "title": "Advanced CS",
            "summary": "Advanced topics",
        },
    )
    db.session.commit()
    q_other = _make_approved_question(instructor_user, other_course, content="Other Course Q")

    assessment = create_assessment(
        instructor_user,
        course.id,
        {"title": "Course 1 Exam", "assessment_type": "MIDTERM"},
    )
    db.session.commit()

    with pytest.raises(
        AssessmentValidationError, match="Cannot assign question from a different course"
    ):
        assign_question(
            instructor_user,
            assessment.public_id,
            {"question_id": str(q_other.public_id)},
        )


def test_publish_gate_validation_failures(
    app: Flask, course: Course, instructor_user: User
) -> None:
    """Publish rules engine ensures assessment has questions and positive total points."""
    assessment = create_assessment(
        instructor_user,
        course.id,
        {"title": "Gate Check Exam", "assessment_type": "QUIZ"},
    )
    db.session.commit()

    # 1. Empty assessment (0 questions) -> rejected
    with pytest.raises(AssessmentValidationError, match="at least one question"):
        publish_assessment(instructor_user, assessment.public_id)


def test_publish_gate_success(app: Flask, course: Course, instructor_user: User) -> None:
    """Valid assessment publishes cleanly and transitions status to PUBLISHED."""
    assessment = create_assessment(
        instructor_user,
        course.id,
        {"title": "Valid Quiz", "assessment_type": "QUIZ"},
    )
    sec = create_section(
        instructor_user,
        assessment.public_id,
        {"title": "Part 1", "position": 1},
    )
    q1 = _make_approved_question(instructor_user, course, content="Gate Q1")
    assign_question(
        instructor_user,
        assessment.public_id,
        {"question_id": str(q1.public_id), "section_id": sec.id, "points": 10.0},
    )
    db.session.commit()

    pub = publish_assessment(instructor_user, assessment.public_id)
    db.session.commit()

    assert pub.status == "PUBLISHED"
    assert pub.published_at is not None

    # Audit event recorded
    audit = (
        db.session.query(AuditEvent)
        .filter(AuditEvent.target_id == pub.id, AuditEvent.action == "ASSESSMENT_PUBLISHED")
        .first()
    )
    assert audit is not None


def test_timing_freeze_invariant(app: Flask, course: Course, instructor_user: User) -> None:
    """After publishing, timing fields are locked; close_at can only be extended."""
    now = datetime.now(UTC)
    open_at = now + timedelta(days=1)
    close_at = now + timedelta(days=2)

    assessment = create_assessment(
        instructor_user,
        course.id,
        {
            "title": "Timing Freeze Quiz",
            "assessment_type": "QUIZ",
            "open_at": open_at.isoformat(),
            "close_at": close_at.isoformat(),
            "time_limit_minutes": 45,
            "attempt_limit": 1,
        },
    )
    q1 = _make_approved_question(instructor_user, course, content="Timing Q1")
    assign_question(
        instructor_user,
        assessment.public_id,
        {"question_id": str(q1.public_id), "points": 5.0},
    )
    publish_assessment(instructor_user, assessment.public_id)
    db.session.commit()

    # Attempt to change locked timing fields
    with pytest.raises(AssessmentLockedError, match="open_at.*locked"):
        update_assessment(
            instructor_user,
            assessment.public_id,
            {"open_at": (now + timedelta(days=3)).isoformat()},
        )

    with pytest.raises(AssessmentLockedError, match="time_limit_minutes.*locked"):
        update_assessment(
            instructor_user,
            assessment.public_id,
            {"time_limit_minutes": 60},
        )

    with pytest.raises(AssessmentLockedError, match="attempt_limit.*locked"):
        update_assessment(
            instructor_user,
            assessment.public_id,
            {"attempt_limit": 2},
        )

    # Attempt to shorten close_at (earlier than current close_at)
    with pytest.raises(AssessmentLockedError, match="close_at can only be extended"):
        update_assessment(
            instructor_user,
            assessment.public_id,
            {"close_at": (now + timedelta(days=1, hours=12)).isoformat()},
        )

    # Extending close_at forward is allowed
    extended_close = close_at + timedelta(days=1)
    updated = update_assessment(
        instructor_user,
        assessment.public_id,
        {"close_at": extended_close.isoformat()},
    )
    db.session.commit()
    assert updated.close_at is not None


def test_structural_freeze_invariant(app: Flask, course: Course, instructor_user: User) -> None:
    """When first attempt starts, all structural mutations are frozen."""
    assessment = create_assessment(
        instructor_user,
        course.id,
        {"title": "Structure Freeze Quiz", "assessment_type": "QUIZ"},
    )
    sec = create_section(
        instructor_user,
        assessment.public_id,
        {"title": "Section 1", "position": 1},
    )
    q1 = _make_approved_question(instructor_user, course, content="Frozen Q1")
    assign_question(
        instructor_user,
        assessment.public_id,
        {"question_id": str(q1.public_id), "section_id": sec.id, "points": 5.0},
    )
    publish_assessment(instructor_user, assessment.public_id)
    db.session.commit()

    # Simulate first attempt started
    assessment.first_attempt_started_at = datetime.now(UTC)
    db.session.commit()

    q2 = _make_approved_question(instructor_user, course, content="Frozen Q2")

    # Adding question must raise AssessmentLockedError
    with pytest.raises(AssessmentLockedError, match="cannot be modified after student attempt"):
        assign_question(
            instructor_user,
            assessment.public_id,
            {"question_id": str(q2.public_id), "section_id": sec.id},
        )

    # Removing question must raise AssessmentLockedError
    with pytest.raises(AssessmentLockedError, match="cannot be removed after student attempt"):
        remove_question_assignment(instructor_user, assessment.public_id, q1.id)

    # Adding section must raise AssessmentLockedError
    with pytest.raises(AssessmentLockedError, match="cannot be added after student attempt"):
        create_section(
            instructor_user,
            assessment.public_id,
            {"title": "Section 2", "position": 2},
        )

    # Deleting section must raise AssessmentLockedError
    with pytest.raises(AssessmentLockedError, match="cannot be deleted after student attempt"):
        delete_section(instructor_user, assessment.public_id, sec.id)


def test_algorithm_05_blueprint_materialization_and_shortage_rollback(
    app: Flask, course: Course, instructor_user: User
) -> None:
    """Test Algorithm 05 dynamic pool materialization, rule validation, and shortage rollback."""
    assessment = create_assessment(
        instructor_user,
        course.id,
        {"title": "Dynamic Matrix Exam", "assessment_type": "MIDTERM"},
    )
    sec = create_section(
        instructor_user,
        assessment.public_id,
        {"title": "Dynamic Section", "position": 1},
    )
    db.session.commit()

    # Create 2 REMEMBER questions and 1 UNDERSTAND question
    _make_approved_question(instructor_user, course, content="Rem 1", difficulty="REMEMBER")
    _make_approved_question(instructor_user, course, content="Rem 2", difficulty="REMEMBER")
    _make_approved_question(instructor_user, course, content="Und 1", difficulty="UNDERSTAND")

    # Configure blueprint requiring 2 REMEMBER (pts: 2.0) and 1 UNDERSTAND (pts: 5.0)
    configure_blueprint(
        instructor_user,
        assessment.public_id,
        {
            "name": "Midterm Blueprint",
            "rules": [
                {
                    "section_id": sec.id,
                    "difficulty": "REMEMBER",
                    "question_type": "SINGLE_CHOICE",
                    "question_count": 2,
                    "points_each": 2.0,
                },
                {
                    "section_id": sec.id,
                    "difficulty": "UNDERSTAND",
                    "question_type": "SINGLE_CHOICE",
                    "question_count": 1,
                    "points_each": 5.0,
                },
            ],
        },
    )
    db.session.commit()

    # Materialize candidate pool
    pool_items = materialize_blueprint_pool(instructor_user, assessment.public_id)
    db.session.commit()
    assert len(pool_items) == 3

    serialized = _serialize_assessment(assessment, full=True)
    assert serialized["questions_count"] == 3
    assert serialized["total_points"] == 9.0  # 2*2 + 1*5

    # Shortage test: update blueprint to require 5 UNDERSTAND questions when only 1 exists
    configure_blueprint(
        instructor_user,
        assessment.public_id,
        {
            "name": "Midterm Blueprint",
            "rules": [
                {
                    "section_id": sec.id,
                    "difficulty": "UNDERSTAND",
                    "question_type": "SINGLE_CHOICE",
                    "question_count": 5,
                    "points_each": 5.0,
                }
            ],
        },
    )
    db.session.commit()

    # Must raise BlueprintValidationError and roll back
    with pytest.raises(BlueprintValidationError, match="Insufficient questions"):
        materialize_blueprint_pool(instructor_user, assessment.public_id)


def test_assessment_lifecycle_cancellation(
    app: Flask, course: Course, instructor_user: User
) -> None:
    """Test state transition: DRAFT -> PUBLISHED -> CANCELLED."""
    assessment = create_assessment(
        instructor_user,
        course.id,
        {"title": "Lifecycle Assessment", "assessment_type": "QUIZ"},
    )
    q = _make_approved_question(instructor_user, course, content="Life Q1")
    assign_question(
        instructor_user,
        assessment.public_id,
        {"question_id": str(q.public_id), "points": 1.0},
    )
    publish_assessment(instructor_user, assessment.public_id)
    db.session.commit()

    # Cancel
    canc = cancel_assessment(instructor_user, assessment.public_id, reason="Technical issue")
    db.session.commit()
    assert canc.status == "CANCELLED"
    assert canc.cancel_reason == "Technical issue"
    assert canc.cancelled_at is not None


def test_trash_and_30_day_restore_policy(app: Flask, course: Course, instructor_user: User) -> None:
    """Test soft-delete to TRASH and 30-day restore eligibility."""
    assessment = create_assessment(
        instructor_user,
        course.id,
        {"title": "Trash Me", "assessment_type": "PRACTICE"},
    )
    db.session.commit()

    # Trash
    trashed = trash_assessment(instructor_user, assessment.public_id)
    db.session.commit()
    assert trashed.status == "TRASH"
    assert trashed.deleted_at is not None

    # Restore within 30 days
    restored = restore_assessment(instructor_user, assessment.public_id)
    db.session.commit()
    assert restored.status == "DRAFT"
    assert restored.deleted_at is None

    # Simulate expired > 30 days
    trashed2 = trash_assessment(instructor_user, assessment.public_id)
    trashed2.deleted_at = datetime.now(UTC) - timedelta(days=31)
    trashed2.restore_until = datetime.now(UTC) - timedelta(days=1)
    db.session.commit()

    with pytest.raises(AssessmentValidationError, match="30-day restore window"):
        restore_assessment(instructor_user, assessment.public_id)
