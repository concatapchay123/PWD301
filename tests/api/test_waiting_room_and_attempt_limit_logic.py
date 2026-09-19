"""TDD Tests for Waiting Room and Attempt Limit Logic.

Verifies:
1. GET /student/assessments/<assessment_id> provides attempt limit metadata:
   - attempts_count, attempt_limit, remaining_attempts, is_attempt_limit_reached, can_start.
   - list of previous attempts and latest_attempt_id.
2. When student exhausts attempt limit (e.g. 3/3):
   - is_attempt_limit_reached is True, remaining_attempts is 0, can_start is False.
3. Student Dashboard (get_student_learning_overview):
   - Excludes assessments from upcoming/to-do list when attempt limit is exhausted or passed.
4. GET /student/assessments list view includes attempt limit metadata.
"""

from __future__ import annotations

from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Enrollment, EnrollmentPeriod
from pwd301.models.types import utc_now
from pwd301.seeds.baseline import seed_baseline
from pwd301.services.analytics_service import get_student_learning_overview
from pwd301.services.assessment_service import (
    assign_question,
    create_assessment,
    publish_assessment,
)
from pwd301.services.attempt_service import start_assessment_attempt, submit_assessment_attempt
from pwd301.services.course_service import create_course
from pwd301.services.question_bank_service import create_question
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def waiting_room_env(app: Flask) -> dict[str, Any]:
    """Setup test fixture with instructor, student, course, and a 2-attempt assessment."""
    sess: Session = db.session
    seed_baseline(sess)

    inst_user = register_user(
        email="instructor_wr@pwd301.local",
        password="Password@123",
        display_name="TS. WR Instructor",
        session=sess,
    )
    assign_role_to_user(inst_user.id, "INSTRUCTOR", session=sess)

    student_user = register_user(
        email="student_wr@pwd301.local",
        password="Password@123",
        display_name="Le WR Student",
        session=sess,
    )
    assign_role_to_user(student_user.id, "STUDENT", session=sess)

    course = create_course(
        actor=inst_user,
        data={
            "course_code": "WR101",
            "title": "Waiting Room Logic Test",
            "category": "Computer Science",
            "capacity": 50,
        },
        session=sess,
    )
    course.status = "PUBLISHED"
    sess.flush()

    enr = Enrollment(
        student_user_id=student_user.id,
        course_id=course.id,
        status="ACTIVE",
    )
    sess.add(enr)
    sess.flush()

    period = EnrollmentPeriod(
        enrollment_id=enr.id,
        period_no=1,
        started_at=utc_now(),
        status="ACTIVE",
    )
    sess.add(period)
    sess.flush()
    enr.current_period_id = period.id
    sess.flush()

    # Question
    q1 = create_question(
        actor=inst_user,
        course_id=course.id,
        payload={
            "question_type": "SINGLE_CHOICE",
            "difficulty": "UNDERSTAND",
            "content": "What decorator creates a route?",
            "choices": [
                {"content": "@app.route", "is_correct": True, "position": 1},
                {"content": "@app.get", "is_correct": False, "position": 2},
            ],
            "default_points": 10.0,
        },
        session=sess,
    )

    # Assessment with attempt_limit = 2
    assessment = create_assessment(
        actor=inst_user,
        course_id=course.id,
        payload={
            "title": "Khao thi Co gioi han Luot thi",
            "assessment_type": "QUIZ",
            "time_limit_minutes": 30,
            "attempt_limit": 2,
            "scoring_policy": "HIGHEST",
            "score_release_policy": "IMMEDIATE",
            "passing_percent": 50.0,
        },
        session=sess,
    )
    assign_question(
        actor=inst_user,
        assessment_id=assessment.id,
        payload={"question_id": q1.id, "points_assigned": 10.0},
        session=sess,
    )
    publish_assessment(actor=inst_user, assessment_id=assessment.id, session=sess)
    sess.commit()

    return {
        "instructor": inst_user,
        "student": student_user,
        "course": course,
        "assessment": assessment,
        "question": q1,
        "enrollment": enr,
        "period": period,
    }


def login_client(client: FlaskClient, email: str, password: str = "Password@123") -> str:
    """Log in client and return csrf token."""
    res = client.post("/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    data = res.get_json()
    return data.get("csrf_token", "")


def test_assessment_detail_provides_attempt_limit_metadata_initially(
    app: Flask, client: FlaskClient, waiting_room_env: dict[str, Any]
) -> None:
    """Before taking any attempt, detail endpoint returns 0 attempts and can_start True."""
    assess = waiting_room_env["assessment"]
    login_client(client, "student_wr@pwd301.local")

    resp = client.get(f"/student/assessments/{assess.public_id}")
    assert resp.status_code == 200
    data = resp.get_json()

    assert data["assessment_id"] == str(assess.public_id)
    assert data["attempt_limit"] == 2
    assert data["attempts_count"] == 0
    assert data["remaining_attempts"] == 2
    assert data["is_attempt_limit_reached"] is False
    assert data["can_start"] is True
    assert isinstance(data["attempts"], list)
    assert len(data["attempts"]) == 0
    assert data["latest_attempt_id"] is None


def test_assessment_detail_and_dashboard_when_attempt_limit_exhausted(
    app: Flask, client: FlaskClient, waiting_room_env: dict[str, Any]
) -> None:
    """When student uses all allowed attempts (2/2):
    1. is_attempt_limit_reached should be True, remaining_attempts 0, can_start False.
    2. latest_attempt_id should point to the last attempt.
    3. get_student_learning_overview should exclude it from upcoming_assessments.
    """
    student = waiting_room_env["student"]
    assess = waiting_room_env["assessment"]
    sess = db.session

    login_client(client, "student_wr@pwd301.local")

    # Attempt 1: Start and submit
    att1, lease1 = start_assessment_attempt(
        student_actor=student, assessment_id=assess.id, session=sess
    )
    submit_assessment_attempt(
        actor=student,
        attempt_id=att1.id,
        raw_lease_token=lease1,
        session=sess,
    )
    sess.commit()

    # Check detail after Attempt 1 (1 of 2 used)
    resp1 = client.get(f"/student/assessments/{assess.public_id}")
    assert resp1.status_code == 200
    data1 = resp1.get_json()
    assert data1["attempts_count"] == 1
    assert data1["remaining_attempts"] == 1
    assert data1["is_attempt_limit_reached"] is False
    assert data1["can_start"] is True
    assert len(data1["attempts"]) == 1
    assert data1["latest_attempt_id"] == str(att1.public_id)

    # Attempt 2: Start and submit (now 2 of 2 used -> exhausted)
    att2, lease2 = start_assessment_attempt(
        student_actor=student, assessment_id=assess.id, session=sess
    )
    submit_assessment_attempt(
        actor=student,
        attempt_id=att2.id,
        raw_lease_token=lease2,
        session=sess,
    )
    sess.commit()

    # Check detail after Attempt 2
    resp2 = client.get(f"/student/assessments/{assess.public_id}")
    assert resp2.status_code == 200
    data2 = resp2.get_json()
    assert data2["attempts_count"] == 2
    assert data2["remaining_attempts"] == 0
    assert data2["is_attempt_limit_reached"] is True
    assert data2["can_start"] is False
    assert len(data2["attempts"]) == 2
    assert data2["latest_attempt_id"] == str(att2.public_id)

    # Dashboard overview should exclude this assessment from upcoming_assessments
    overview = get_student_learning_overview(student, session=sess)
    upcoming_ids = [u["assessment_id"] for u in overview["upcoming_assessments"]]
    assert str(assess.public_id) not in upcoming_ids


def test_student_assessments_list_contains_attempt_limit_metadata(
    app: Flask, client: FlaskClient, waiting_room_env: dict[str, Any]
) -> None:
    """GET /student/assessments should include attempt limit metadata for each item."""
    assess = waiting_room_env["assessment"]
    login_client(client, "student_wr@pwd301.local")

    resp = client.get("/student/assessments")
    assert resp.status_code == 200
    data = resp.get_json()

    items = data.get("items", [])
    matching = [item for item in items if item["assessment_id"] == str(assess.public_id)]
    assert len(matching) == 1
    item = matching[0]

    assert item["attempt_limit"] == 2
    assert "attempts_count" in item
    assert "remaining_attempts" in item
    assert "is_attempt_limit_reached" in item
