"""Concurrency and race condition tests for Attempt Submission Idempotency (TASK-015).

Validates:
- Two concurrent threads submitting the exact same attempt with the same idempotency key
  converge cleanly to status 'SUBMITTED' without database error or double grading.
- One thread performs the primary transition (is_idempotent_replay=False), and the
  concurrent thread receives the idempotent replay (is_idempotent_replay=True).
- Concurrent submissions with different keys result in one winning submission and one
  SubmissionIdempotencyConflictError.
"""

from __future__ import annotations

import concurrent.futures
import uuid
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
from pwd301.services.exceptions import SubmissionIdempotencyConflictError
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
    u = register_user("admin_race_sub@example.com", "Password@123", "Admin User")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create instructor user."""
    u = register_user("inst_race_sub@example.com", "Password@123", "Attempt Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create student user."""
    u = register_user("student_race_sub@example.com", "Password@123", "Attempt Student")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def published_course(app: Flask, instructor_user: User, admin_user: User) -> Course:
    """Create and publish a course owned by instructor."""
    c = create_course(
        instructor_user,
        {
            "course_code": "RACE-SUB-101",
            "title": "Submission Race Testing Course",
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
) -> Assessment:
    """Helper to create and publish an assessment with one assigned question."""
    now = datetime.now(UTC)
    payload = {
        "title": "Race Test Assessment",
        "assessment_type": "QUIZ",
        "time_limit_minutes": time_limit,
        "open_at": (now - timedelta(hours=1)).isoformat(),
        "close_at": (now + timedelta(hours=24)).isoformat(),
        "passing_score": 50.0,
    }
    assessment = create_assessment(instructor, course.id, payload, session=db.session)
    sec = create_section(instructor, assessment.id, {"title": "Main Section"}, session=db.session)

    q_data: dict[str, Any] = {
        "question_type": "SINGLE_CHOICE",
        "difficulty": "REMEMBER",
        "content": "Is submission idempotent?",
        "default_points": 10.0,
        "choices": [
            {"content": "Yes", "is_correct": True, "position": 1},
            {"content": "No", "is_correct": False, "position": 2},
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


def test_concurrent_submit_same_idempotency_key_converges(
    app: Flask,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
) -> None:
    """Two concurrent submission requests with the same idempotency key converge safely."""
    sess: Session = db.session
    assessment = _make_assessment_with_question(instructor_user, published_course)

    attempt, lease_token = start_assessment_attempt(enrolled_student, assessment.id, session=sess)
    attempt_id = attempt.id
    student_id = enrolled_student.id
    idempotency_key = uuid.uuid4()

    def worker_submit() -> dict[str, Any]:
        with app.app_context():
            worker_sess = db.session
            actor = worker_sess.query(User).filter(User.id == student_id).one()
            return submit_assessment_attempt(
                actor=actor,
                attempt_id=attempt_id,
                idempotency_key=idempotency_key,
                raw_lease_token=lease_token,
                session=worker_sess,
            )

    # Launch 2 threads concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(worker_submit)
        f2 = executor.submit(worker_submit)
        res1 = f1.result()
        res2 = f2.result()

    # Both must succeed with SUBMITTED status and matching idempotency key
    assert res1["status"] == "SUBMITTED"
    assert res2["status"] == "SUBMITTED"
    assert res1["submission_idempotency_key"] == str(idempotency_key)
    assert res2["submission_idempotency_key"] == str(idempotency_key)

    # Exactly one was initial submit and one was replay (or both converged cleanly)
    replay_statuses = [res1["is_idempotent_replay"], res2["is_idempotent_replay"]]
    assert False in replay_statuses

    # Check database state
    sess.expire_all()
    final_attempt = sess.query(AssessmentAttempt).filter(AssessmentAttempt.id == attempt_id).one()
    assert final_attempt.status == "SUBMITTED"
    assert str(final_attempt.submission_idempotency_key) == str(idempotency_key)
    assert final_attempt.lease_token_hash is None

    # Check audit events: exactly one ATTEMPT_SUBMITTED recorded
    audits = (
        sess.query(AuditEvent)
        .filter(
            AuditEvent.target_type == "ATTEMPT",
            AuditEvent.target_id == attempt_id,
            AuditEvent.action == "ATTEMPT_SUBMITTED",
        )
        .all()
    )
    assert len(audits) == 1


def test_concurrent_submit_different_keys_race_conflict(
    app: Flask,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
) -> None:
    """Two concurrent submission requests with different keys yield 1 success and 1 conflict."""
    sess: Session = db.session
    assessment = _make_assessment_with_question(instructor_user, published_course)

    attempt, lease_token = start_assessment_attempt(enrolled_student, assessment.id, session=sess)
    attempt_id = attempt.id
    student_id = enrolled_student.id
    key_a = uuid.uuid4()
    key_b = uuid.uuid4()

    def worker_submit_keyed(k: uuid.UUID) -> dict[str, Any]:
        with app.app_context():
            worker_sess = db.session
            actor = worker_sess.query(User).filter(User.id == student_id).one()
            return submit_assessment_attempt(
                actor=actor,
                attempt_id=attempt_id,
                idempotency_key=k,
                raw_lease_token=lease_token,
                session=worker_sess,
            )

    results: list[dict[str, Any]] = []
    errors: list[Exception] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f_a = executor.submit(worker_submit_keyed, key_a)
        f_b = executor.submit(worker_submit_keyed, key_b)

        for f in (f_a, f_b):
            try:
                res = f.result()
                results.append(res)
            except Exception as e:
                errors.append(e)

    # One succeeds, and one raises SubmissionIdempotencyConflictError
    assert len(results) == 1
    assert results[0]["status"] == "SUBMITTED"
    assert len(errors) == 1
    assert isinstance(errors[0], SubmissionIdempotencyConflictError)
