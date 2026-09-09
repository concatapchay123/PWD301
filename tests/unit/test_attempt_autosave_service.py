"""Unit tests for Attempt Autosave, Event Sourcing & Offline Reconciliation (TASK-015).

Validates:
- Autosave text answer and multiple-choice answer.
- Stale sequence rejection (client_sequence <= last_client_sequence) with StaleAnswerSequenceError.
- Immutable AttemptAnswerEvent record generation for accepted and rejected operations.
- Offline batch reconciliation with order sorting and stale filtering.
- Lease token, lease epoch, and server deadline enforcement during autosave/sync.
- Rejection of autosave operations on already submitted attempts.
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
from pwd301.models.attempt_regrade import (
    AttemptAnswer,
    AttemptAnswerChoice,
    AttemptAnswerEvent,
)
from pwd301.models.course import Course
from pwd301.models.identity import Role, User
from pwd301.services.assessment_service import (
    assign_question,
    create_assessment,
    create_section,
    publish_assessment,
)
from pwd301.services.attempt_service import (
    save_attempt_answer,
    start_assessment_attempt,
    submit_assessment_attempt,
    sync_offline_answers,
)
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.exceptions import (
    AttemptAlreadySubmittedError,
    AttemptExpiredError,
    AttemptLeaseConflictError,
    StaleAnswerSequenceError,
    StaleLeaseEpochError,
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
    u = register_user("admin_autosave@example.com", "Password@123", "Admin User")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create instructor user."""
    u = register_user("inst_autosave@example.com", "Password@123", "Attempt Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create student user."""
    u = register_user("student_autosave@example.com", "Password@123", "Attempt Student")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def published_course(app: Flask, instructor_user: User, admin_user: User) -> Course:
    """Create and publish a course owned by instructor."""
    c = create_course(
        instructor_user,
        {
            "course_code": "AUTOSAVE-101",
            "title": "Autosave Testing Course",
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


def _make_assessment_with_questions(
    instructor: User,
    course: Course,
    time_limit: int | None = 60,
    open_delta_hours: int = -1,
    close_delta_hours: int = 24,
) -> Assessment:
    """Helper to create and publish an assessment with MCQ and essay questions."""
    now = datetime.now(UTC)
    payload = {
        "title": "Autosave Test Assessment",
        "assessment_type": "QUIZ",
        "time_limit_minutes": time_limit,
        "open_at": (now + timedelta(hours=open_delta_hours)).isoformat(),
        "close_at": (now + timedelta(hours=close_delta_hours)).isoformat(),
        "passing_score": 50.0,
    }
    assessment = create_assessment(instructor, course.id, payload, session=db.session)
    sec = create_section(instructor, assessment.id, {"title": "Section A"}, session=db.session)

    # Question 1: Multiple Choice
    q1_data: dict[str, Any] = {
        "question_type": "SINGLE_CHOICE",
        "difficulty": "REMEMBER",
        "content": "Which protocol is used for web browsing?",
        "default_points": 5.0,
        "choices": [
            {"content": "HTTP", "is_correct": True, "position": 1},
            {"content": "FTP", "is_correct": False, "position": 2},
            {"content": "SMTP", "is_correct": False, "position": 3},
        ],
    }
    q1 = create_question(instructor, course.id, q1_data, session=db.session)
    assign_question(
        instructor,
        assessment.id,
        {"question_id": q1.id, "points_assigned": 5.0, "section_id": sec.id},
        session=db.session,
    )

    # Question 2: Essay
    q2_data: dict[str, Any] = {
        "question_type": "ESSAY",
        "difficulty": "UNDERSTAND",
        "content": "Explain the concept of idempotency in distributed systems.",
        "default_points": 10.0,
    }
    q2 = create_question(instructor, course.id, q2_data, session=db.session)
    assign_question(
        instructor,
        assessment.id,
        {"question_id": q2.id, "points_assigned": 10.0, "section_id": sec.id},
        session=db.session,
    )

    publish_assessment(instructor, assessment.id, session=db.session)
    db.session.commit()
    return assessment


def test_autosave_text_answer(
    app: Flask,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
) -> None:
    """Autosave text answer persists AttemptAnswer and creates accepted AttemptAnswerEvent."""
    sess: Session = db.session
    assessment = _make_assessment_with_questions(instructor_user, published_course)

    attempt, lease_token = start_assessment_attempt(enrolled_student, assessment.id, session=sess)
    essay_aq = [aq for aq in attempt.attempt_questions if aq.question_type_snapshot == "ESSAY"][0]

    change_id = uuid.uuid4()
    payload = {
        "client_sequence": 1,
        "client_change_id": str(change_id),
        "answer_text": "Idempotency means repeated execution has the same effect.",
    }

    result = save_attempt_answer(
        actor=enrolled_student,
        attempt_id=attempt.id,
        attempt_question_id=essay_aq.public_id,
        payload=payload,
        raw_lease_token=lease_token,
        session=sess,
    )

    assert result["answer_version"] == 1
    assert result["last_client_sequence"] == 1
    assert result["lease_epoch"] == 1

    # Verify persisted AttemptAnswer
    ans = sess.query(AttemptAnswer).filter(AttemptAnswer.attempt_question_id == essay_aq.id).first()
    assert ans is not None
    assert ans.answer_text == "Idempotency means repeated execution has the same effect."
    assert ans.answer_version == 1
    assert ans.last_client_sequence == 1

    # Verify accepted AttemptAnswerEvent
    event = (
        sess.query(AttemptAnswerEvent)
        .filter(
            AttemptAnswerEvent.attempt_question_id == essay_aq.id,
            AttemptAnswerEvent.change_id == change_id,
        )
        .first()
    )
    assert event is not None
    assert event.accepted is True
    assert event.client_sequence == 1
    assert event.server_answer_version == 1
    assert event.rejection_reason is None


def test_autosave_multiple_choice_answer(
    app: Flask,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
) -> None:
    """Autosave MCQ updates AttemptAnswer and junction table AttemptAnswerChoice."""
    sess: Session = db.session
    assessment = _make_assessment_with_questions(instructor_user, published_course)

    attempt, lease_token = start_assessment_attempt(enrolled_student, assessment.id, session=sess)
    mcq_aq = [
        aq for aq in attempt.attempt_questions if aq.question_type_snapshot == "SINGLE_CHOICE"
    ][0]
    choice_snapshot = mcq_aq.choice_snapshots[0]

    change_id = uuid.uuid4()
    payload = {
        "client_sequence": 1,
        "client_change_id": str(change_id),
        "selected_choice_keys": [str(choice_snapshot.choice_key_snapshot)],
    }

    result = save_attempt_answer(
        actor=enrolled_student,
        attempt_id=attempt.id,
        attempt_question_id=mcq_aq.public_id,
        payload=payload,
        raw_lease_token=lease_token,
        session=sess,
    )

    assert result["answer_version"] == 1
    assert result["last_client_sequence"] == 1

    # Verify junction row
    ans = sess.query(AttemptAnswer).filter(AttemptAnswer.attempt_question_id == mcq_aq.id).first()
    assert ans is not None
    choices = (
        sess.query(AttemptAnswerChoice)
        .filter(AttemptAnswerChoice.attempt_answer_id == ans.id)
        .all()
    )
    assert len(choices) == 1
    assert choices[0].attempt_choice_snapshot_id == choice_snapshot.id


def test_autosave_stale_sequence_rejection(
    app: Flask,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
) -> None:
    """Autosave with client_sequence <= last_client_sequence raises 409 STALE_ANSWER."""
    sess: Session = db.session
    assessment = _make_assessment_with_questions(instructor_user, published_course)

    attempt, lease_token = start_assessment_attempt(enrolled_student, assessment.id, session=sess)
    essay_aq = [aq for aq in attempt.attempt_questions if aq.question_type_snapshot == "ESSAY"][0]

    # Save sequence 2
    save_attempt_answer(
        actor=enrolled_student,
        attempt_id=attempt.id,
        attempt_question_id=essay_aq.public_id,
        payload={
            "client_sequence": 2,
            "client_change_id": str(uuid.uuid4()),
            "answer_text": "First save at sequence 2",
        },
        raw_lease_token=lease_token,
        session=sess,
    )

    # Attempt to save stale sequence 1
    stale_change_id = uuid.uuid4()
    with pytest.raises(StaleAnswerSequenceError) as exc_info:
        save_attempt_answer(
            actor=enrolled_student,
            attempt_id=attempt.id,
            attempt_question_id=essay_aq.public_id,
            payload={
                "client_sequence": 1,
                "client_change_id": str(stale_change_id),
                "answer_text": "Stale late arrival at sequence 1",
            },
            raw_lease_token=lease_token,
            session=sess,
        )
    assert "Stale answer sequence" in str(exc_info.value)

    # Verify answer was NOT overwritten
    ans = sess.query(AttemptAnswer).filter(AttemptAnswer.attempt_question_id == essay_aq.id).first()
    assert ans is not None
    assert ans.answer_text == "First save at sequence 2"
    assert ans.last_client_sequence == 2

    # Verify rejected AttemptAnswerEvent was recorded with STALE reason
    event = (
        sess.query(AttemptAnswerEvent)
        .filter(
            AttemptAnswerEvent.attempt_question_id == essay_aq.id,
            AttemptAnswerEvent.change_id == stale_change_id,
        )
        .first()
    )
    assert event is not None
    assert event.accepted is False
    assert event.rejection_reason == "STALE"


def test_autosave_duplicate_change_id_idempotency(
    app: Flask,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
) -> None:
    """Re-submitting the exact same client_change_id returns original saved result idempotently."""
    sess: Session = db.session
    assessment = _make_assessment_with_questions(instructor_user, published_course)

    attempt, lease_token = start_assessment_attempt(enrolled_student, assessment.id, session=sess)
    essay_aq = [aq for aq in attempt.attempt_questions if aq.question_type_snapshot == "ESSAY"][0]

    change_id = uuid.uuid4()
    payload = {
        "client_sequence": 1,
        "client_change_id": str(change_id),
        "answer_text": "Initial answer text",
    }

    res1 = save_attempt_answer(
        actor=enrolled_student,
        attempt_id=attempt.id,
        attempt_question_id=essay_aq.public_id,
        payload=payload,
        raw_lease_token=lease_token,
        session=sess,
    )
    assert res1["answer_version"] == 1

    # Retry with same change_id
    res2 = save_attempt_answer(
        actor=enrolled_student,
        attempt_id=attempt.id,
        attempt_question_id=essay_aq.public_id,
        payload=payload,
        raw_lease_token=lease_token,
        session=sess,
    )
    assert res2["answer_version"] == 1
    assert res2["last_client_sequence"] == 1


def test_autosave_stale_lease_epoch_rejection(
    app: Flask,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
) -> None:
    """Sending a stale lease_epoch raises StaleLeaseEpochError."""
    sess: Session = db.session
    assessment = _make_assessment_with_questions(instructor_user, published_course)

    attempt, lease_token = start_assessment_attempt(enrolled_student, assessment.id, session=sess)
    attempt.lease_epoch = 2
    sess.commit()

    essay_aq = [aq for aq in attempt.attempt_questions if aq.question_type_snapshot == "ESSAY"][0]

    with pytest.raises(StaleLeaseEpochError):
        save_attempt_answer(
            actor=enrolled_student,
            attempt_id=attempt.id,
            attempt_question_id=essay_aq.public_id,
            payload={
                "client_sequence": 1,
                "client_change_id": str(uuid.uuid4()),
                "answer_text": "Testing lease epoch",
                "lease_epoch": 1,  # Stale epoch (current is 2)
            },
            raw_lease_token=lease_token,
            session=sess,
        )


def test_autosave_rejected_on_invalid_lease_token(
    app: Flask,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
) -> None:
    """Autosave with wrong or missing lease token raises AttemptLeaseConflictError."""
    sess: Session = db.session
    assessment = _make_assessment_with_questions(instructor_user, published_course)

    attempt, _ = start_assessment_attempt(enrolled_student, assessment.id, session=sess)
    essay_aq = [aq for aq in attempt.attempt_questions if aq.question_type_snapshot == "ESSAY"][0]

    with pytest.raises(AttemptLeaseConflictError):
        save_attempt_answer(
            actor=enrolled_student,
            attempt_id=attempt.id,
            attempt_question_id=essay_aq.public_id,
            payload={"client_sequence": 1, "answer_text": "Answer"},
            raw_lease_token="bad_token_1234567890",
            session=sess,
        )


def test_autosave_rejected_on_submitted_attempt(
    app: Flask,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
) -> None:
    """Autosave on an already SUBMITTED attempt raises AttemptAlreadySubmittedError."""
    sess: Session = db.session
    assessment = _make_assessment_with_questions(instructor_user, published_course)

    attempt, lease_token = start_assessment_attempt(enrolled_student, assessment.id, session=sess)
    submit_assessment_attempt(
        actor=enrolled_student,
        attempt_id=attempt.id,
        idempotency_key=uuid.uuid4(),
        session=sess,
    )

    essay_aq = [aq for aq in attempt.attempt_questions if aq.question_type_snapshot == "ESSAY"][0]

    with pytest.raises(AttemptAlreadySubmittedError):
        save_attempt_answer(
            actor=enrolled_student,
            attempt_id=attempt.id,
            attempt_question_id=essay_aq.public_id,
            payload={"client_sequence": 1, "answer_text": "Late answer"},
            raw_lease_token=lease_token,
            session=sess,
        )


def test_autosave_rejected_after_deadline_expired(
    app: Flask,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
) -> None:
    """Autosave after deadline_at transitions attempt to EXPIRED and raises AttemptExpiredError."""
    sess: Session = db.session
    assessment = _make_assessment_with_questions(instructor_user, published_course)

    attempt, lease_token = start_assessment_attempt(enrolled_student, assessment.id, session=sess)
    attempt.started_at = datetime.now(UTC) - timedelta(hours=2)
    attempt.deadline_at = datetime.now(UTC) - timedelta(minutes=5)
    sess.commit()

    essay_aq = [aq for aq in attempt.attempt_questions if aq.question_type_snapshot == "ESSAY"][0]

    with pytest.raises(AttemptExpiredError):
        save_attempt_answer(
            actor=enrolled_student,
            attempt_id=attempt.id,
            attempt_question_id=essay_aq.public_id,
            payload={"client_sequence": 1, "answer_text": "Overdue answer"},
            raw_lease_token=lease_token,
            session=sess,
        )

    # Verify attempt transitioned to EXPIRED
    sess.refresh(attempt)
    assert attempt.status == "EXPIRED"


def test_sync_offline_answers_batch(
    app: Flask,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
) -> None:
    """sync_offline_answers reconciles a batch of out-of-order answers and skips stale ones."""
    sess: Session = db.session
    assessment = _make_assessment_with_questions(instructor_user, published_course)

    attempt, lease_token = start_assessment_attempt(enrolled_student, assessment.id, session=sess)
    essay_aq = [aq for aq in attempt.attempt_questions if aq.question_type_snapshot == "ESSAY"][0]
    mcq_aq = [
        aq for aq in attempt.attempt_questions if aq.question_type_snapshot == "SINGLE_CHOICE"
    ][0]
    choice_snapshot = mcq_aq.choice_snapshots[0]

    # Pre-save essay question at sequence 2
    save_attempt_answer(
        actor=enrolled_student,
        attempt_id=attempt.id,
        attempt_question_id=essay_aq.public_id,
        payload={
            "client_sequence": 2,
            "client_change_id": str(uuid.uuid4()),
            "answer_text": "Server already has sequence 2",
        },
        raw_lease_token=lease_token,
        session=sess,
    )

    # Prepare offline batch:
    # 1. Essay sequence 1 (stale, should be skipped)
    # 2. MCQ sequence 1 (valid, should be synced)
    # 3. Essay sequence 3 (valid newer, should be synced)
    batch = [
        {
            "attempt_question_id": str(essay_aq.public_id),
            "client_sequence": 3,
            "client_change_id": str(uuid.uuid4()),
            "answer_text": "Newest sequence 3 from offline sync",
        },
        {
            "attempt_question_id": str(essay_aq.public_id),
            "client_sequence": 1,
            "client_change_id": str(uuid.uuid4()),
            "answer_text": "Stale sequence 1 from offline sync",
        },
        {
            "attempt_question_id": str(mcq_aq.public_id),
            "client_sequence": 1,
            "client_change_id": str(uuid.uuid4()),
            "selected_choice_keys": [str(choice_snapshot.choice_key_snapshot)],
        },
    ]

    result = sync_offline_answers(
        actor=enrolled_student,
        attempt_id=attempt.id,
        answers_batch=batch,
        raw_lease_token=lease_token,
        session=sess,
    )

    assert result["synced_count"] == 2
    assert result["skipped_count"] == 1
    assert len(result["synced"]) == 2
    assert len(result["skipped"]) == 1

    # Verify final state on essay question
    ans = sess.query(AttemptAnswer).filter(AttemptAnswer.attempt_question_id == essay_aq.id).first()
    assert ans is not None
    assert ans.last_client_sequence == 3
    assert ans.answer_text == "Newest sequence 3 from offline sync"
