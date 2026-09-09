"""Security & IDOR Negative Tests for Attempt Autosave & Submission Engine (TASK-015).

Validates:
- Fail-closed Zero-Trust IDOR protection on autosave, sync, and submit endpoints.
- Peer students enrolled in the same course receive ForbiddenError (403).
- Instructors and admins receive ForbiddenError (403) on student autosave/submit.
- Unauthenticated requests receive 401 Unauthorized.
- ADR-002: Zero leakage of internal BIGINT PK/FK identifiers across all service and API payloads.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
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
    save_attempt_answer,
    start_assessment_attempt,
    submit_assessment_attempt,
    sync_offline_answers,
)
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.exceptions import ForbiddenError
from pwd301.services.jwt_auth_service import create_token_pair
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
    u = register_user("admin_idor_sub@example.com", "Password@123", "Admin User")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create instructor user."""
    u = register_user("inst_idor_sub@example.com", "Password@123", "Attempt Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_owner(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create attempt owner student."""
    u = register_user("owner_idor_sub@example.com", "Password@123", "Attempt Owner")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def peer_student(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create peer student enrolled in the same course."""
    u = register_user("peer_idor_sub@example.com", "Password@123", "Peer Student")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def published_course(app: Flask, instructor_user: User, admin_user: User) -> Course:
    """Create and publish a course owned by instructor."""
    c = create_course(
        instructor_user,
        {
            "course_code": "IDOR-SUB-101",
            "title": "IDOR Submission Testing Course",
            "summary": "Core Course",
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
    """Enroll both student owner and peer student into course."""
    enroll_student(student_owner, published_course.id, session=db.session)
    enroll_student(peer_student, published_course.id, session=db.session)
    db.session.commit()
    return student_owner, peer_student


def _make_assessment_with_question(
    instructor: User,
    course: Course,
    time_limit: int | None = 60,
) -> Assessment:
    """Helper to create and publish an assessment with one assigned question."""
    now = datetime.now(UTC)
    payload = {
        "title": "IDOR Test Assessment",
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
        "content": "Which HTTP status code is Forbidden?",
        "default_points": 10.0,
        "choices": [
            {"content": "403", "is_correct": True, "position": 1},
            {"content": "401", "is_correct": False, "position": 2},
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


def test_peer_student_cannot_autosave_answer(
    app: Flask,
    instructor_user: User,
    enrolled_students: tuple[User, User],
    published_course: Course,
) -> None:
    """Peer student attempting to autosave on another student's attempt is blocked with 403."""
    sess: Session = db.session
    student_owner, peer_student = enrolled_students
    assessment = _make_assessment_with_question(instructor_user, published_course)

    attempt, lease_token = start_assessment_attempt(student_owner, assessment.id, session=sess)
    aq = attempt.attempt_questions[0]

    with pytest.raises(ForbiddenError):
        save_attempt_answer(
            actor=peer_student,
            attempt_id=attempt.id,
            attempt_question_id=aq.public_id,
            payload={"client_sequence": 1, "answer_text": "Malicious edit"},
            raw_lease_token=lease_token,
            session=sess,
        )


def test_peer_student_cannot_sync_offline_answers(
    app: Flask,
    instructor_user: User,
    enrolled_students: tuple[User, User],
    published_course: Course,
) -> None:
    """Peer student attempting to batch sync answers on another student is blocked with 403."""
    sess: Session = db.session
    student_owner, peer_student = enrolled_students
    assessment = _make_assessment_with_question(instructor_user, published_course)

    attempt, lease_token = start_assessment_attempt(student_owner, assessment.id, session=sess)
    aq = attempt.attempt_questions[0]

    with pytest.raises(ForbiddenError):
        sync_offline_answers(
            actor=peer_student,
            attempt_id=attempt.id,
            answers_batch=[
                {
                    "attempt_question_id": str(aq.public_id),
                    "client_sequence": 1,
                    "answer_text": "Bad",
                }
            ],
            raw_lease_token=lease_token,
            session=sess,
        )


def test_peer_student_cannot_submit_attempt(
    app: Flask,
    instructor_user: User,
    enrolled_students: tuple[User, User],
    published_course: Course,
) -> None:
    """Peer student attempting to submit another student's attempt is blocked with 403."""
    sess: Session = db.session
    student_owner, peer_student = enrolled_students
    assessment = _make_assessment_with_question(instructor_user, published_course)

    attempt, lease_token = start_assessment_attempt(student_owner, assessment.id, session=sess)

    with pytest.raises(ForbiddenError):
        submit_assessment_attempt(
            actor=peer_student,
            attempt_id=attempt.id,
            idempotency_key=uuid.uuid4(),
            raw_lease_token=lease_token,
            session=sess,
        )


def test_instructor_and_admin_cannot_autosave_or_submit_student_attempt(
    app: Flask,
    instructor_user: User,
    admin_user: User,
    enrolled_students: tuple[User, User],
    published_course: Course,
) -> None:
    """Instructors and admins cannot masquerade or submit answers for student attempts."""
    sess: Session = db.session
    student_owner, _ = enrolled_students
    assessment = _make_assessment_with_question(instructor_user, published_course)

    attempt, lease_token = start_assessment_attempt(student_owner, assessment.id, session=sess)
    aq = attempt.attempt_questions[0]

    # Instructor blocked from autosave and submit
    with pytest.raises(ForbiddenError):
        save_attempt_answer(
            actor=instructor_user,
            attempt_id=attempt.id,
            attempt_question_id=aq.public_id,
            payload={"client_sequence": 1, "answer_text": "Instructor edit"},
            raw_lease_token=lease_token,
            session=sess,
        )

    with pytest.raises(ForbiddenError):
        submit_assessment_attempt(
            actor=instructor_user,
            attempt_id=attempt.id,
            idempotency_key=uuid.uuid4(),
            session=sess,
        )

    # Admin blocked from autosave and submit
    with pytest.raises(ForbiddenError):
        save_attempt_answer(
            actor=admin_user,
            attempt_id=attempt.id,
            attempt_question_id=aq.public_id,
            payload={"client_sequence": 1, "answer_text": "Admin edit"},
            raw_lease_token=lease_token,
            session=sess,
        )

    with pytest.raises(ForbiddenError):
        submit_assessment_attempt(
            actor=admin_user,
            attempt_id=attempt.id,
            idempotency_key=uuid.uuid4(),
            session=sess,
        )


def test_api_unauthenticated_and_peer_forbidden(
    client: FlaskClient,
    instructor_user: User,
    enrolled_students: tuple[User, User],
    published_course: Course,
) -> None:
    """REST API enforces 401 for unauthenticated requests and 403 for peer student IDOR attempts."""
    sess: Session = db.session
    student_owner, peer_student = enrolled_students
    assessment = _make_assessment_with_question(instructor_user, published_course)

    attempt, lease_token = start_assessment_attempt(student_owner, assessment.id, session=sess)
    aq = attempt.attempt_questions[0]

    attempt_uuid = str(attempt.public_id)
    aq_uuid = str(aq.public_id)

    # 1. Unauthenticated requests -> 401
    put_resp = client.put(f"/api/attempts/{attempt_uuid}/answers/{aq_uuid}", json={})
    assert put_resp.status_code == 401

    sync_resp = client.post(f"/api/attempts/{attempt_uuid}/answers/sync", json={"answers": []})
    assert sync_resp.status_code == 401

    sub_resp = client.post(f"/api/attempts/{attempt_uuid}/submit", json={})
    assert sub_resp.status_code == 401

    # 2. Peer student authenticated requests -> 403
    peer_tokens = create_token_pair(peer_student, session=sess)
    peer_auth = {"Authorization": f"Bearer {peer_tokens['access_token']}"}

    peer_put = client.put(
        f"/api/attempts/{attempt_uuid}/answers/{aq_uuid}",
        json={"client_sequence": 1, "answer_text": "Hacked"},
        headers={**peer_auth, "X-Attempt-Lease-Token": lease_token},
    )
    assert peer_put.status_code == 403
    assert peer_put.get_json()["error"]["code"] == "FORBIDDEN"

    peer_sync = client.post(
        f"/api/attempts/{attempt_uuid}/answers/sync",
        json={"answers": [{"attempt_question_id": aq_uuid, "client_sequence": 1}]},
        headers={**peer_auth, "X-Attempt-Lease-Token": lease_token},
    )
    assert peer_sync.status_code == 403
    assert peer_sync.get_json()["error"]["code"] == "FORBIDDEN"

    peer_sub = client.post(
        f"/api/attempts/{attempt_uuid}/submit",
        json={"idempotency_key": str(uuid.uuid4())},
        headers={**peer_auth, "X-Attempt-Lease-Token": lease_token},
    )
    assert peer_sub.status_code == 403
    assert peer_sub.get_json()["error"]["code"] == "FORBIDDEN"


def test_adr002_zero_bigint_leakage_in_responses(
    app: Flask,
    instructor_user: User,
    enrolled_students: tuple[User, User],
    published_course: Course,
) -> None:
    """ADR-002 enforcement: autosave and submission results expose no integer PKs."""
    sess: Session = db.session
    student_owner, _ = enrolled_students
    assessment = _make_assessment_with_question(instructor_user, published_course)

    attempt, lease_token = start_assessment_attempt(student_owner, assessment.id, session=sess)
    aq = attempt.attempt_questions[0]

    save_res = save_attempt_answer(
        actor=student_owner,
        attempt_id=attempt.id,
        attempt_question_id=aq.public_id,
        payload={"client_sequence": 1, "answer_text": "Answer"},
        raw_lease_token=lease_token,
        session=sess,
    )

    # All identifiers must be valid UUID strings
    assert uuid.UUID(save_res["attempt_id"])
    assert uuid.UUID(save_res["attempt_question_id"])
    assert "id" not in save_res
    assert "attempt_pk" not in save_res
    assert "question_pk" not in save_res

    sub_res = submit_assessment_attempt(
        actor=student_owner,
        attempt_id=attempt.id,
        idempotency_key=uuid.uuid4(),
        raw_lease_token=lease_token,
        session=sess,
    )
    assert uuid.UUID(sub_res["attempt_id"])
    assert uuid.UUID(sub_res["submission_idempotency_key"])
    assert "id" not in sub_res
    assert "pk" not in sub_res
