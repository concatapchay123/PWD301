"""Integration tests for Assessment Attempt Lease Management REST API endpoints (TASK-014).

Validates:
- POST /api/attempts/<attempt_id>/lease/heartbeat (Header and JSON body token delivery).
- POST /api/attempts/<attempt_id>/heartbeat (08_ATTEMPT_API.md alias).
- POST /api/attempts/<attempt_id>/lease/takeover and POST /api/attempts/<attempt_id>/lease.
- POST /api/attempts/<attempt_id>/lease/release.
- Conflict enforcement (409 LEASE_CONFLICT on stale token or tab race).
- Server deadline enforcement (409 DEADLINE_EXPIRED).
- Zero-trust IDOR defense (403 FORBIDDEN for non-owning student or instructor).
- ADR-002 compliance: zero leakage of internal BIGINT PKs or FKs across all endpoints.
"""

from __future__ import annotations

import re
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
from pwd301.services.attempt_service import start_assessment_attempt
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

            if k in ("attempt_id", "assessment_id", "course_id") and v is not None:
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
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Instructor User."""
    u = register_user("api_lease_inst@example.com", "Password@123", "Attempt API Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Student User A."""
    u = register_user("api_lease_stud_a@example.com", "Password@123", "Student API User A")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def student_user_b(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create Student User B (peer)."""
    u = register_user("api_lease_stud_b@example.com", "Password@123", "Student API User B")
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def student_headers(student_user: User) -> dict[str, str]:
    """JWT headers for Student A."""
    tokens = create_token_pair(student_user)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def student_b_headers(student_user_b: User) -> dict[str, str]:
    """JWT headers for Student B."""
    tokens = create_token_pair(student_user_b)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def instructor_headers(instructor_user: User) -> dict[str, str]:
    """JWT headers for Instructor."""
    tokens = create_token_pair(instructor_user)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def published_course(app: Flask, instructor_user: User, setup_roles: dict[str, Role]) -> Course:
    """Create and publish a course owned by instructor."""
    admin = register_user("api_lease_admin@example.com", "Password@123", "Admin User")
    admin = assign_role_to_user(admin.id, "ADMIN")

    c = create_course(
        instructor_user,
        {
            "course_code": "API-LEASE-101",
            "title": "API Lease Course",
            "summary": "API Course",
        },
    )
    change_course_status(instructor_user, c.id, "SUBMITTED_FOR_REVIEW")
    change_course_status(admin, c.id, "APPROVED")
    change_course_status(admin, c.id, "PUBLISHED")
    db.session.commit()
    return c


@pytest.fixture
def enrolled_students(
    app: Flask,
    student_user: User,
    student_user_b: User,
    published_course: Course,
) -> tuple[User, User]:
    """Enroll both students in published course."""
    enroll_student(student_user, published_course.id, session=db.session)
    enroll_student(student_user_b, published_course.id, session=db.session)
    db.session.commit()
    return student_user, student_user_b


def _make_assessment_with_question(instructor: User, course: Course) -> Assessment:
    """Helper to create and publish an assessment with one assigned question."""
    now = datetime.now(UTC)
    payload = {
        "title": "API Lease Assessment",
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
        "content": "API Lease Question",
        "default_points": 10.0,
        "choices": [
            {"content": "Alpha", "is_correct": True, "position": 1},
            {"content": "Beta", "is_correct": False, "position": 2},
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


def test_heartbeat_via_header_success(
    client: FlaskClient,
    student_user: User,
    student_headers: dict[str, str],
    instructor_user: User,
    published_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """POST /api/attempts/<id>/lease/heartbeat with X-Attempt-Lease-Token header returns 200 OK."""
    assessment = _make_assessment_with_question(instructor_user, published_course)
    attempt, token = start_assessment_attempt(student_user, assessment.id, session=db.session)

    headers = {**student_headers, "X-Attempt-Lease-Token": token}
    resp = client.post(f"/api/attempts/{attempt.public_id}/lease/heartbeat", headers=headers)

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["attempt_id"] == str(attempt.public_id)
    assert data["status"] == "IN_PROGRESS"
    assert "lease_expires_at" in data
    assert "server_time" in data
    assert data["remaining_seconds"] is not None
    assert_adr002_clean(data)


def test_heartbeat_via_json_body_success(
    client: FlaskClient,
    student_user: User,
    student_headers: dict[str, str],
    instructor_user: User,
    published_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """POST /api/attempts/<id>/lease/heartbeat with JSON body token returns 200 OK."""
    assessment = _make_assessment_with_question(instructor_user, published_course)
    attempt, token = start_assessment_attempt(student_user, assessment.id, session=db.session)

    resp = client.post(
        f"/api/attempts/{attempt.public_id}/lease/heartbeat",
        headers=student_headers,
        json={"lease_token": token},
    )

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["attempt_id"] == str(attempt.public_id)
    assert data["status"] == "IN_PROGRESS"
    assert_adr002_clean(data)


def test_heartbeat_alias_route_success(
    client: FlaskClient,
    student_user: User,
    student_headers: dict[str, str],
    instructor_user: User,
    published_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """POST /api/attempts/<id>/heartbeat per 08_ATTEMPT_API.md alias returns 200 OK."""
    assessment = _make_assessment_with_question(instructor_user, published_course)
    attempt, token = start_assessment_attempt(student_user, assessment.id, session=db.session)

    headers = {**student_headers, "X-Attempt-Lease-Token": token}
    resp = client.post(f"/api/attempts/{attempt.public_id}/heartbeat", headers=headers)

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "IN_PROGRESS"
    assert_adr002_clean(data)


def test_heartbeat_stale_token_returns_409_lease_conflict(
    client: FlaskClient,
    student_user: User,
    student_headers: dict[str, str],
    instructor_user: User,
    published_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """POST /api/attempts/<id>/lease/heartbeat with stale token returns 409 LEASE_CONFLICT."""
    assessment = _make_assessment_with_question(instructor_user, published_course)
    attempt, _ = start_assessment_attempt(student_user, assessment.id, session=db.session)

    headers = {**student_headers, "X-Attempt-Lease-Token": "invalid_hex_token_12345"}
    resp = client.post(f"/api/attempts/{attempt.public_id}/lease/heartbeat", headers=headers)

    assert resp.status_code == 409
    data = resp.get_json()
    assert data["error"]["code"] == "LEASE_CONFLICT"
    assert "taken over" in data["error"]["message"].lower()


def test_takeover_route_success_and_invalidates_old_tab(
    client: FlaskClient,
    student_user: User,
    student_headers: dict[str, str],
    instructor_user: User,
    published_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """POST /api/attempts/<id>/lease/takeover returns new token; old tab receives 409."""
    assessment = _make_assessment_with_question(instructor_user, published_course)
    attempt, old_token = start_assessment_attempt(student_user, assessment.id, session=db.session)

    # Takeover from Tab 2
    takeover_resp = client.post(
        f"/api/attempts/{attempt.public_id}/lease/takeover",
        headers=student_headers,
        json={},
    )
    assert takeover_resp.status_code == 200
    t_data = takeover_resp.get_json()
    assert t_data["attempt_id"] == str(attempt.public_id)
    assert t_data["status"] == "IN_PROGRESS"
    new_token = t_data["lease_token"]
    assert new_token != old_token
    assert len(new_token) == 64
    assert_adr002_clean(t_data)

    # Tab 1 sends heartbeat with old token -> 409 LEASE_CONFLICT
    tab1_headers = {**student_headers, "X-Attempt-Lease-Token": old_token}
    hb_resp = client.post(
        f"/api/attempts/{attempt.public_id}/lease/heartbeat", headers=tab1_headers
    )
    assert hb_resp.status_code == 409
    assert hb_resp.get_json()["error"]["code"] == "LEASE_CONFLICT"

    # Tab 2 sends heartbeat with new token -> 200 OK
    tab2_headers = {**student_headers, "X-Attempt-Lease-Token": new_token}
    hb2_resp = client.post(
        f"/api/attempts/{attempt.public_id}/lease/heartbeat", headers=tab2_headers
    )
    assert hb2_resp.status_code == 200


def test_takeover_alias_route_success(
    client: FlaskClient,
    student_user: User,
    student_headers: dict[str, str],
    instructor_user: User,
    published_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """POST /api/attempts/<id>/lease per 08_ATTEMPT_API.md alias returns 200 OK."""
    assessment = _make_assessment_with_question(instructor_user, published_course)
    attempt, _ = start_assessment_attempt(student_user, assessment.id, session=db.session)

    resp = client.post(
        f"/api/attempts/{attempt.public_id}/lease",
        headers=student_headers,
        json={},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "lease_token" in data
    assert_adr002_clean(data)


def test_release_route_success(
    client: FlaskClient,
    student_user: User,
    student_headers: dict[str, str],
    instructor_user: User,
    published_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """POST /api/attempts/<id>/lease/release clears lease cleanly."""
    assessment = _make_assessment_with_question(instructor_user, published_course)
    attempt, token = start_assessment_attempt(student_user, assessment.id, session=db.session)

    headers = {**student_headers, "X-Attempt-Lease-Token": token}
    resp = client.post(f"/api/attempts/{attempt.public_id}/lease/release", headers=headers)

    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Lease released successfully."

    # Subsequent heartbeat fails with 409 LEASE_CONFLICT
    hb_resp = client.post(f"/api/attempts/{attempt.public_id}/lease/heartbeat", headers=headers)
    assert hb_resp.status_code == 409


def test_release_route_wrong_token_returns_409(
    client: FlaskClient,
    student_user: User,
    student_headers: dict[str, str],
    instructor_user: User,
    published_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """POST /api/attempts/<id>/lease/release with wrong token returns 409 LEASE_CONFLICT."""
    assessment = _make_assessment_with_question(instructor_user, published_course)
    attempt, _ = start_assessment_attempt(student_user, assessment.id, session=db.session)

    headers = {**student_headers, "X-Attempt-Lease-Token": "bad_token"}
    resp = client.post(f"/api/attempts/{attempt.public_id}/lease/release", headers=headers)
    assert resp.status_code == 409
    assert resp.get_json()["error"]["code"] == "LEASE_CONFLICT"


def test_unauthenticated_requests_return_401(
    client: FlaskClient,
    student_user: User,
    instructor_user: User,
    published_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """Missing JWT authorization returns 401 UNAUTHORIZED across all lease routes."""
    assessment = _make_assessment_with_question(instructor_user, published_course)
    attempt, token = start_assessment_attempt(student_user, assessment.id, session=db.session)

    r1 = client.post(f"/api/attempts/{attempt.public_id}/lease/heartbeat")
    assert r1.status_code == 401

    r2 = client.post(f"/api/attempts/{attempt.public_id}/lease/takeover")
    assert r2.status_code == 401

    r3 = client.post(f"/api/attempts/{attempt.public_id}/lease/release")
    assert r3.status_code == 401


def test_idor_peer_and_instructor_return_403(
    client: FlaskClient,
    student_user: User,
    student_b_headers: dict[str, str],
    instructor_headers: dict[str, str],
    instructor_user: User,
    published_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """Peer student and instructor receive 403 FORBIDDEN when attempting lease operations."""
    assessment = _make_assessment_with_question(instructor_user, published_course)
    attempt, token = start_assessment_attempt(student_user, assessment.id, session=db.session)

    headers_peer = {**student_b_headers, "X-Attempt-Lease-Token": token}
    headers_inst = {**instructor_headers, "X-Attempt-Lease-Token": token}

    # Peer student
    assert (
        client.post(
            f"/api/attempts/{attempt.public_id}/lease/heartbeat", headers=headers_peer
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/api/attempts/{attempt.public_id}/lease/takeover", headers=headers_peer
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/api/attempts/{attempt.public_id}/lease/release", headers=headers_peer
        ).status_code
        == 403
    )

    # Instructor
    assert (
        client.post(
            f"/api/attempts/{attempt.public_id}/lease/heartbeat", headers=headers_inst
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/api/attempts/{attempt.public_id}/lease/takeover", headers=headers_inst
        ).status_code
        == 403
    )


def test_deadline_expired_returns_409_deadline_expired(
    client: FlaskClient,
    student_user: User,
    student_headers: dict[str, str],
    instructor_user: User,
    published_course: Course,
    enrolled_students: tuple[User, User],
) -> None:
    """Heartbeat or takeover after deadline returns 409 DEADLINE_EXPIRED."""
    assessment = _make_assessment_with_question(instructor_user, published_course)
    attempt, token = start_assessment_attempt(student_user, assessment.id, session=db.session)

    # Force past deadline preserving started_at <= deadline_at
    now = datetime.now(UTC)
    attempt.started_at = now - timedelta(hours=2)
    attempt.deadline_at = now - timedelta(hours=1)
    db.session.commit()

    headers = {**student_headers, "X-Attempt-Lease-Token": token}
    resp = client.post(f"/api/attempts/{attempt.public_id}/lease/heartbeat", headers=headers)
    assert resp.status_code == 409
    data = resp.get_json()
    assert data["error"]["code"] == "DEADLINE_EXPIRED"
