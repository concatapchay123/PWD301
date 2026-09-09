"""Integration tests for Assessment Attempt Autosave, Sync & Submission REST APIs (TASK-015).

Validates end-to-end attempt lifecycle:
- POST /api/assessments/<assessment_id>/attempts -> Start attempt and acquire lease.
- PUT /api/attempts/<attempt_id>/answers/<attempt_question_id> -> Autosave answers.
- 409 STALE_ANSWER on stale client_sequence.
- POST /api/attempts/<attempt_id>/answers/sync -> Offline batch reconciliation.
- POST /api/attempts/<attempt_id>/submit -> Idempotent submission with header or body key.
- Repeated submit with same key -> 200 OK with is_idempotent_replay=True.
- Submit with different key after submission -> 409 SUBMISSION_CONFLICT.
- Autosave after submission blocked with 409 STATE_VIOLATION.
- ADR-002 compliance: zero leakage of internal BIGINT PKs across all endpoints.
"""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.assessment import Assessment
from pwd301.models.attempt_regrade import AssessmentAttempt
from pwd301.models.course import Course
from pwd301.models.identity import Role, User
from pwd301.services.assessment_service import (
    assign_question,
    create_assessment,
    create_section,
    publish_assessment,
)
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.question_bank_service import create_question
from pwd301.services.user_service import assign_role_to_user, register_user

UUID_REGEX = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def assert_adr002_clean(data: Any) -> None:
    """Recursively verify no internal BIGINT PKs, FKs, or answers leak (ADR-002)."""
    if isinstance(data, dict):
        for k, v in data.items():
            assert k != "id", f"Internal primary key 'id' leaked: {data}"
            assert k != "creator_user_id", f"Internal FK 'creator_user_id' leaked: {data}"
            assert k != "student_user_id", f"Internal FK 'student_user_id' leaked: {data}"
            assert k != "course_internal_id", f"Internal FK 'course_internal_id' leaked: {data}"
            assert k != "is_correct", f"Security violation: 'is_correct' leaked: {data}"
            assert k != "explanation", f"Security violation: 'explanation' leaked: {data}"
            assert k != "lease_token_hash", f"Security violation: 'lease_token_hash' leaked: {data}"

            if k in ("attempt_id", "assessment_id", "attempt_question_id") and v is not None:
                assert isinstance(v, str), f"Field '{k}' should be string, got {type(v)}: {v}"
                assert UUID_REGEX.match(v), f"Field '{k}' is not a valid UUID: {v}"

            assert_adr002_clean(v)
    elif isinstance(data, list):
        for item in data:
            assert_adr002_clean(item)


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
    u = register_user("admin_api_sub@example.com", "Password@123", "Admin User")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create instructor user."""
    u = register_user("inst_api_sub@example.com", "Password@123", "Attempt Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create student user."""
    u = register_user("student_api_sub@example.com", "Password@123", "Attempt Student")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def published_course(app: Flask, instructor_user: User, admin_user: User) -> Course:
    """Create and publish a course owned by instructor."""
    c = create_course(
        instructor_user,
        {
            "course_code": "API-SUB-101",
            "title": "API Submission Testing Course",
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


@pytest.fixture
def auth_headers(app: Flask, enrolled_student: User) -> dict[str, str]:
    """Generate JWT authentication headers for student."""
    tokens = create_token_pair(enrolled_student, session=db.session)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def _make_assessment_with_questions(
    instructor: User,
    course: Course,
    time_limit: int | None = 60,
) -> Assessment:
    """Helper to create and publish an assessment with MCQ and essay questions."""
    now = datetime.now(UTC)
    payload = {
        "title": "API Submission Test Assessment",
        "assessment_type": "QUIZ",
        "time_limit_minutes": time_limit,
        "open_at": (now - timedelta(hours=1)).isoformat(),
        "close_at": (now + timedelta(hours=24)).isoformat(),
        "passing_score": 50.0,
    }
    assessment = create_assessment(instructor, course.id, payload, session=db.session)
    sec = create_section(instructor, assessment.id, {"title": "Main Section"}, session=db.session)

    # MCQ question
    q1_data: dict[str, Any] = {
        "question_type": "SINGLE_CHOICE",
        "difficulty": "REMEMBER",
        "content": "Which HTTP method is idempotent?",
        "default_points": 5.0,
        "choices": [
            {"content": "PUT", "is_correct": True, "position": 1},
            {"content": "POST", "is_correct": False, "position": 2},
        ],
    }
    q1 = create_question(instructor, course.id, q1_data, session=db.session)
    assign_question(
        instructor,
        assessment.id,
        {"question_id": q1.id, "points_assigned": 5.0, "section_id": sec.id},
        session=db.session,
    )

    # Essay question
    q2_data: dict[str, Any] = {
        "question_type": "ESSAY",
        "difficulty": "UNDERSTAND",
        "content": "Explain idempotent API design.",
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


def test_full_lifecycle_start_autosave_sync_submit(
    client: FlaskClient,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
    auth_headers: dict[str, str],
) -> None:
    """Full lifecycle: Start -> Autosave answers -> Offline sync -> Idempotent submit."""
    assessment = _make_assessment_with_questions(instructor_user, published_course)
    assess_uuid = str(assessment.public_id)

    # 1. Start Attempt
    start_resp = client.post(
        f"/api/assessments/{assess_uuid}/attempts",
        headers=auth_headers,
    )
    assert start_resp.status_code == 201
    start_data = start_resp.get_json()
    assert_adr002_clean(start_data)

    attempt_id = start_data["attempt_id"]
    raw_lease_token = start_data["raw_lease_token"]
    questions = start_data["questions"]
    assert len(questions) == 2
    mcq_q = [q for q in questions if q["question_type"] == "SINGLE_CHOICE"][0]
    essay_q = [q for q in questions if q["question_type"] == "ESSAY"][0]

    lease_header = {"X-Attempt-Lease-Token": raw_lease_token}

    # 2. Autosave MCQ Answer
    mcq_choice_key = mcq_q["choices"][0]["choice_key"]
    save_mcq_resp = client.put(
        f"/api/attempts/{attempt_id}/answers/{mcq_q['attempt_question_id']}",
        json={
            "client_sequence": 1,
            "client_change_id": str(uuid.uuid4()),
            "selected_choice_keys": [mcq_choice_key],
        },
        headers={**auth_headers, **lease_header},
    )
    assert save_mcq_resp.status_code == 200
    mcq_result = save_mcq_resp.get_json()
    assert_adr002_clean(mcq_result)
    assert mcq_result["answer_version"] == 1
    assert mcq_result["last_client_sequence"] == 1

    # 3. Autosave Essay Answer (passing lease token in body)
    save_essay_resp = client.put(
        f"/api/attempts/{attempt_id}/answers/{essay_q['attempt_question_id']}",
        json={
            "client_sequence": 1,
            "client_change_id": str(uuid.uuid4()),
            "answer_text": "Idempotent operations can be applied multiple times.",
            "lease_token": raw_lease_token,
        },
        headers=auth_headers,
    )
    assert save_essay_resp.status_code == 200
    essay_result = save_essay_resp.get_json()
    assert_adr002_clean(essay_result)
    assert essay_result["answer_version"] == 1

    # 4. Reject Stale Sequence on Essay Question
    stale_resp = client.put(
        f"/api/attempts/{attempt_id}/answers/{essay_q['attempt_question_id']}",
        json={
            "client_sequence": 1,
            "client_change_id": str(uuid.uuid4()),
            "answer_text": "Old stale rewrite",
        },
        headers={**auth_headers, **lease_header},
    )
    assert stale_resp.status_code == 409
    assert stale_resp.get_json()["error"]["code"] == "STALE_ANSWER"

    # 5. Offline Batch Reconciliation Sync
    sync_resp = client.post(
        f"/api/attempts/{attempt_id}/answers/sync",
        json={
            "answers": [
                {
                    "attempt_question_id": essay_q["attempt_question_id"],
                    "client_sequence": 2,
                    "client_change_id": str(uuid.uuid4()),
                    "answer_text": "Updated essay answer sequence 2 via sync",
                },
                {
                    "attempt_question_id": essay_q["attempt_question_id"],
                    "client_sequence": 1,  # Stale
                    "client_change_id": str(uuid.uuid4()),
                    "answer_text": "Stale sequence 1 via sync",
                },
            ]
        },
        headers={**auth_headers, **lease_header},
    )
    assert sync_resp.status_code == 200
    sync_data = sync_resp.get_json()
    assert_adr002_clean(sync_data)
    assert sync_data["synced_count"] == 1
    assert sync_data["skipped_count"] == 1

    # 6. Idempotent Submit via Header Key
    idempotency_key = str(uuid.uuid4())
    sub_resp1 = client.post(
        f"/api/attempts/{attempt_id}/submit",
        headers={
            **auth_headers,
            **lease_header,
            "X-Submission-Idempotency-Key": idempotency_key,
        },
    )
    assert sub_resp1.status_code == 200
    sub_data1 = sub_resp1.get_json()
    assert_adr002_clean(sub_data1)
    assert sub_data1["status"] in ("SUBMITTED", "GRADED", "PENDING_GRADING")
    assert sub_data1["is_idempotent_replay"] is False
    assert sub_data1["submission_idempotency_key"] == idempotency_key

    # 7. Repeated Submit with Same Key -> Idempotent Replay (200 OK)
    sub_resp2 = client.post(
        f"/api/attempts/{attempt_id}/submit",
        headers={
            **auth_headers,
            "X-Submission-Idempotency-Key": idempotency_key,
        },
    )
    assert sub_resp2.status_code == 200
    sub_data2 = sub_resp2.get_json()
    assert_adr002_clean(sub_data2)
    assert sub_data2["status"] in ("SUBMITTED", "GRADED", "PENDING_GRADING")
    assert sub_data2["is_idempotent_replay"] is True
    assert sub_data2["submitted_at"] == sub_data1["submitted_at"]

    # 8. Submit with Different Key -> 409 Conflict
    sub_resp3 = client.post(
        f"/api/attempts/{attempt_id}/submit",
        headers={
            **auth_headers,
            "X-Submission-Idempotency-Key": str(uuid.uuid4()),
        },
    )
    assert sub_resp3.status_code == 409
    assert sub_resp3.get_json()["error"]["code"] == "SUBMISSION_CONFLICT"

    # 9. Autosave on Submitted Attempt -> 409 State Violation
    late_save_resp = client.put(
        f"/api/attempts/{attempt_id}/answers/{essay_q['attempt_question_id']}",
        json={
            "client_sequence": 10,
            "answer_text": "Post-submission answer attempt",
        },
        headers={**auth_headers, **lease_header},
    )
    assert late_save_resp.status_code == 409
    assert late_save_resp.get_json()["error"]["code"] == "STATE_VIOLATION"


def test_submit_via_json_body_idempotency_key(
    client: FlaskClient,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
    auth_headers: dict[str, str],
) -> None:
    """Submit attempt with idempotency key supplied in JSON request body."""
    assessment = _make_assessment_with_questions(instructor_user, published_course)
    assess_uuid = str(assessment.public_id)

    start_resp = client.post(
        f"/api/assessments/{assess_uuid}/attempts",
        headers=auth_headers,
    )
    attempt_id = start_resp.get_json()["attempt_id"]
    lease_token = start_resp.get_json()["raw_lease_token"]

    idempotency_key = str(uuid.uuid4())
    sub_resp = client.post(
        f"/api/attempts/{attempt_id}/submit",
        json={
            "idempotency_key": idempotency_key,
            "lease_token": lease_token,
        },
        headers=auth_headers,
    )
    assert sub_resp.status_code == 200
    sub_data = sub_resp.get_json()
    assert sub_data["status"] in ("SUBMITTED", "GRADED", "PENDING_GRADING")
    assert sub_data["submission_idempotency_key"] == idempotency_key
    assert sub_data["is_idempotent_replay"] is False

    # Replay via JSON body
    replay_resp = client.post(
        f"/api/attempts/{attempt_id}/submit",
        json={"idempotency_key": idempotency_key},
        headers=auth_headers,
    )
    assert replay_resp.status_code == 200
    assert replay_resp.get_json()["is_idempotent_replay"] is True


def test_submit_overdue_attempt_returns_409_deadline_expired(
    client: FlaskClient,
    instructor_user: User,
    enrolled_student: User,
    published_course: Course,
    auth_headers: dict[str, str],
) -> None:
    """Submit attempt after deadline passes returns 409 DEADLINE_EXPIRED."""
    sess: Session = db.session
    assessment = _make_assessment_with_questions(instructor_user, published_course)
    assess_uuid = str(assessment.public_id)

    start_resp = client.post(
        f"/api/assessments/{assess_uuid}/attempts",
        headers=auth_headers,
    )
    attempt_id = start_resp.get_json()["attempt_id"]

    # Manually expire deadline
    attempt = (
        sess.query(AssessmentAttempt)
        .filter(AssessmentAttempt.public_id == uuid.UUID(attempt_id))
        .one()
    )
    attempt.started_at = datetime.now(UTC) - timedelta(hours=2)
    attempt.deadline_at = datetime.now(UTC) - timedelta(minutes=5)
    sess.commit()

    sub_resp = client.post(
        f"/api/attempts/{attempt_id}/submit",
        headers={
            **auth_headers,
            "X-Submission-Idempotency-Key": str(uuid.uuid4()),
        },
    )
    assert sub_resp.status_code == 409
    assert sub_resp.get_json()["error"]["code"] == "DEADLINE_EXPIRED"

    sess.refresh(attempt)
    assert attempt.status == "EXPIRED"
