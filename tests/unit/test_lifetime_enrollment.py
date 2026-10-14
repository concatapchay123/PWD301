"""Tests for F02: Lifetime Enrollment REST Lock (ENROLLMENT_LIFETIME_GUARANTEE).

Verifies that voluntary withdrawal from an active course is strictly forbidden (HTTP 403)
across both Web SPA session and REST API (JWT) surfaces, and the enrollment remains ACTIVE.
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Enrollment
from pwd301.seeds.baseline import seed_baseline
from pwd301.services.course_service import create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def lifetime_env(app: Flask) -> dict[str, Any]:
    """Setup instructor, student, and published course with active enrollment."""
    sess: Session = db.session
    seed_baseline(sess)

    inst = register_user(
        f"inst_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Instructor One", session=sess
    )
    assign_role_to_user(inst.id, "INSTRUCTOR", session=sess)

    student = register_user(
        f"student_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Student One", session=sess
    )
    assign_role_to_user(student.id, "STUDENT", session=sess)

    course = create_course(
        actor=inst,
        data={
            "course_code": f"LIFE-{uuid.uuid4().hex[:4].upper()}",
            "title": "Lifetime Enrollment Course",
            "category": "Testing",
            "capacity": 100,
        },
        session=sess,
    )
    course.status = "PUBLISHED"
    sess.commit()

    # Enroll student
    enrollment = enroll_student(actor=student, course_id=course.id, session=sess)
    sess.commit()

    return {
        "instructor": inst,
        "student": student,
        "course": course,
        "enrollment": enrollment,
    }


def test_api_leave_course_returns_403_forbidden(
    client: FlaskClient, lifetime_env: dict[str, Any]
) -> None:
    """POST /api/courses/<id>/leave must return HTTP 403 Forbidden with standard envelope."""
    student = lifetime_env["student"]
    course = lifetime_env["course"]

    tokens = create_token_pair(student)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = client.post(
        f"/api/courses/{course.public_id}/leave",
        headers=headers,
        json={"reason": "Want to leave"},
    )
    assert resp.status_code == 403
    data = resp.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "FORBIDDEN"
    assert "Chức năng rời khóa học đã bị vô hiệu hóa" in data["error"]["message"]

    # Enrollment in DB remains ACTIVE
    enr = (
        db.session.query(Enrollment)
        .filter_by(student_user_id=student.id, course_id=course.id)
        .one()
    )
    assert enr.status == "ACTIVE"


def test_web_leave_course_returns_403_forbidden(
    client: FlaskClient, lifetime_env: dict[str, Any]
) -> None:
    """POST /student/courses/<id>/leave must return HTTP 403 Forbidden."""
    from pwd301.services.session_auth_service import create_auth_session

    student = lifetime_env["student"]
    course = lifetime_env["course"]

    # Session auth
    _, raw_key = create_auth_session(student, session=db.session)
    db.session.commit()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(student.id)
        sess["auth_session_key"] = raw_key
        sess["auth_version"] = student.auth_version
        sess["auth_source"] = "SESSION"

    resp = client.post(
        f"/student/courses/{course.public_id}/leave",
        json={"reason": "Attempt withdrawal"},
        headers={"Accept": "application/json"},
    )
    assert resp.status_code == 403
    data = resp.get_json()
    assert data["error"]["code"] == "FORBIDDEN"

    # Enrollment in DB remains ACTIVE
    enr = (
        db.session.query(Enrollment)
        .filter_by(student_user_id=student.id, course_id=course.id)
        .one()
    )
    assert enr.status == "ACTIVE"


def test_unauthenticated_leave_returns_401(
    client: FlaskClient, lifetime_env: dict[str, Any]
) -> None:
    """Unauthenticated call to /api/courses/<id>/leave must return 401."""
    course = lifetime_env["course"]
    resp = client.post(f"/api/courses/{course.public_id}/leave")
    assert resp.status_code == 401
