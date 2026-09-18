"""Tests for Instructor Role Backend Completion, IDOR Defense, and Exam Results Inspection.

Verifies:
1. GET /instructor/assessments/<assessment_id>/attempts (Student submissions & objective scores).
2. GET /instructor/attempts/<attempt_id>/results (Detailed question-by-question candidate response).
3. IDOR Defense: Cross-instructor access prevention (HTTP 403 Forbidden).
4. ADR-002 Zero Internal PK Leakage compliance across serializers and endpoints.
5. Analytics overview real metrics (total_students, total_questions).
"""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.assessment import Assessment
from pwd301.models.attempt_regrade import AssessmentAttempt
from pwd301.models.identity import User
from pwd301.services.assessment_service import (
    assign_question,
    create_assessment,
    publish_assessment,
)
from pwd301.services.attempt_service import start_assessment_attempt, submit_assessment_attempt
from pwd301.services.course_service import change_course_status, create_course
from pwd301.services.question_bank_service import create_question
from pwd301.services.user_service import assign_role_to_user, register_user

UUID_REGEX = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)


def assert_adr002(data: Any) -> None:
    """Recursively verify no internal BigInt PKs are leaked in responses."""
    if isinstance(data, dict):
        for k, v in data.items():
            assert k != "id", f"Internal primary key leaked: {data}"
            if (
                k.endswith("_id")
                and v is not None
                and k not in ("choice_key", "temp_id", "question_type")
            ):
                assert isinstance(v, str) and UUID_REGEX.match(v), (
                    f"Expected UUID string for {k}, got {type(v)}: {v}"
                )
            assert_adr002(v)
    elif isinstance(data, list):
        for item in data:
            assert_adr002(item)


@pytest.fixture
def instructor_a(app: Flask) -> User:
    """Register primary instructor user."""
    sess: Session = db.session
    u = register_user(
        f"inst_a_{uuid.uuid4().hex[:6]}@example.com",
        "Password@123",
        "Dr. Alice Turing",
    )
    u = assign_role_to_user(u.id, "INSTRUCTOR")
    u.email_verified_at = datetime.now(UTC)
    sess.commit()
    return u


@pytest.fixture
def instructor_b(app: Flask) -> User:
    """Register secondary instructor user for IDOR testing."""
    sess: Session = db.session
    u = register_user(
        f"inst_b_{uuid.uuid4().hex[:6]}@example.com",
        "Password@123",
        "Dr. Bob Shannon",
    )
    u = assign_role_to_user(u.id, "INSTRUCTOR")
    u.email_verified_at = datetime.now(UTC)
    sess.commit()
    return u


@pytest.fixture
def student_candidate(app: Flask) -> User:
    """Register student user who takes the exam."""
    sess: Session = db.session
    u = register_user(
        f"stud_cand_{uuid.uuid4().hex[:6]}@example.com",
        "Password@123",
        "Charlie Learner",
    )
    u = assign_role_to_user(u.id, "STUDENT")
    u.email_verified_at = datetime.now(UTC)
    sess.commit()
    return u


@pytest.fixture
def course_with_exam(
    app: Flask,
    instructor_a: User,
    student_candidate: User,
) -> dict[str, Any]:
    """Create a course with published assessment and a submitted student attempt."""
    sess: Session = db.session

    # 1. Course
    c = create_course(
        actor=instructor_a,
        data={
            "course_code": f"COMP{uuid.uuid4().hex[:4].upper()}",
            "title": "Modern Software Engineering & Distributed Systems",
            "description": "Comprehensive study of distributed architectures.",
            "category": "Technology",
            "difficulty": "ADVANCED",
        },
        session=sess,
    )
    change_course_status(instructor_a, c.id, "SUBMITTED_FOR_REVIEW", session=sess)
    # Admin approval simulation (direct published for test)
    c.status = "PUBLISHED"
    sess.commit()

    # 2. Enrollment
    from pwd301.services.enrollment_service import enroll_student

    enroll_student(student_candidate, c.id, session=sess)
    sess.commit()

    # 3. Objective Questions (SINGLE_CHOICE and MULTIPLE_CHOICE)
    q1 = create_question(
        actor=instructor_a,
        course_id=c.id,
        payload={
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "stem": "Which protocol algorithm provides distributed consensus via leader election?",
            "points": 5.0,
            "choices": [
                {"content": "Raft Protocol", "is_correct": True, "position": 1},
                {"content": "Round Robin", "is_correct": False, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )

    q2 = create_question(
        actor=instructor_a,
        course_id=c.id,
        payload={
            "question_type": "MULTIPLE_CHOICE",
            "difficulty": "APPLY",
            "stem": "Which of the following are ACID properties in relational database systems?",
            "points": 5.0,
            "choices": [
                {"content": "Atomicity", "is_correct": True, "position": 1},
                {"content": "Consistency", "is_correct": True, "position": 2},
                {"content": "Arbitrary Sharding", "is_correct": False, "position": 3},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()

    # 4. Assessment
    asm = create_assessment(
        actor=instructor_a,
        course_id=c.id,
        payload={
            "title": "Midterm Distributed Systems Examination",
            "assessment_type": "MIDTERM",
            "time_limit_minutes": 60,
            "pass_mark_percent": 50.0,
        },
        session=sess,
    )
    assign_question(
        instructor_a,
        asm.id,
        {"question_id": str(q1.public_id), "points": 5.0, "position": 1},
        session=sess,
    )
    assign_question(
        instructor_a,
        asm.id,
        {"question_id": str(q2.public_id), "points": 5.0, "position": 2},
        session=sess,
    )
    publish_assessment(instructor_a, asm.id, session=sess)
    sess.commit()

    # 5. Student Starts and Submits Attempt
    attempt_obj, lease_token = start_assessment_attempt(
        student_actor=student_candidate,
        assessment_id=asm.id,
        session=sess,
    )
    sess.commit()

    from pwd301.services.attempt_service import save_attempt_answer

    # Resolve choices
    c1_correct = [c for c in q1.current_revision.choices if c.is_correct][0]
    c2_correct = [c for c in q2.current_revision.choices if c.is_correct]

    q1_att = [
        q
        for q in attempt_obj.attempt_questions
        if q.source_question_revision_id == q1.current_revision.id
    ][0]
    save_attempt_answer(
        actor=student_candidate,
        attempt_id=attempt_obj.id,
        attempt_question_id=q1_att.id,
        payload={"selected_choice_id": str(c1_correct.public_id)},
        raw_lease_token=lease_token,
        session=sess,
    )

    q2_att = [
        q
        for q in attempt_obj.attempt_questions
        if q.source_question_revision_id == q2.current_revision.id
    ][0]
    save_attempt_answer(
        actor=student_candidate,
        attempt_id=attempt_obj.id,
        attempt_question_id=q2_att.id,
        payload={"selected_choice_ids": [str(c.public_id) for c in c2_correct]},
        raw_lease_token=lease_token,
        session=sess,
    )
    sess.commit()

    # Submit Attempt -> Triggers Objective Auto-grading
    submit_assessment_attempt(
        actor=student_candidate,
        attempt_id=attempt_obj.id,
        raw_lease_token=lease_token,
        session=sess,
    )
    sess.commit()

    return {
        "course": c,
        "assessment": asm,
        "attempt": attempt_obj,
        "q1": q1,
        "q2": q2,
    }


def test_instructor_list_assessment_attempts_api(
    client: FlaskClient,
    instructor_a: User,
    course_with_exam: dict[str, Any],
) -> None:
    """Instructor A can list all candidate attempts and scores for their assessment."""
    asm: Assessment = course_with_exam["assessment"]

    client.post("/auth/login", json={"email": instructor_a.email, "password": "Password@123"})

    resp = client.get(f"/instructor/assessments/{asm.public_id}/attempts")
    assert resp.status_code == 200
    data = resp.get_json()

    assert "attempts" in data
    assert "total" in data
    assert data["total"] == 1
    assert len(data["attempts"]) == 1

    cand = data["attempts"][0]
    assert cand["student_name"] == "Charlie Learner"
    assert cand["raw_score"] == 10.0
    assert cand["max_possible_points"] == 10.0
    assert cand["percentage"] == 100.0
    assert cand["is_passed"] is True
    assert cand["status"] == "GRADED"

    # ADR-002 Zero Internal PK Leakage verification
    assert_adr002(data)


def test_instructor_get_attempt_results_detail_api(
    client: FlaskClient,
    instructor_a: User,
    course_with_exam: dict[str, Any],
) -> None:
    """Instructor A can inspect question-by-question candidate responses and answers."""
    att: AssessmentAttempt = course_with_exam["attempt"]

    client.post("/auth/login", json={"email": instructor_a.email, "password": "Password@123"})

    resp = client.get(f"/instructor/attempts/{att.public_id}/results")
    assert resp.status_code == 200
    data = resp.get_json()

    assert data["student_name"] == "Charlie Learner"
    assert data["status"] == "GRADED"
    assert data["total_awarded_points"] == 10.0
    assert data["total_possible_points"] == 10.0
    assert len(data["questions"]) == 2

    # Check question detail breakdown
    q1_data = [q for q in data["questions"] if "consensus" in q["stem"]][0]
    assert q1_data["question_type"] == "SINGLE_CHOICE"
    assert q1_data["points_assigned"] == 5.0
    assert q1_data["awarded_points"] == 5.0
    assert q1_data["is_correct"] is True

    selected_choice = [c for c in q1_data["choices"] if c["is_selected"]][0]
    assert selected_choice["content"] == "Raft Protocol"
    assert selected_choice["is_correct"] is True

    # ADR-002 Zero Internal PK Leakage verification
    assert_adr002(data)


def test_idor_defense_instructor_cannot_access_other_assessment(
    client: FlaskClient,
    instructor_b: User,
    course_with_exam: dict[str, Any],
) -> None:
    """Instructor B cannot access assessment attempts or results belonging to Instructor A."""
    asm: Assessment = course_with_exam["assessment"]
    att: AssessmentAttempt = course_with_exam["attempt"]

    client.post("/auth/login", json={"email": instructor_b.email, "password": "Password@123"})

    # 1. Attempt to list attempts of other instructor's assessment -> 403
    resp_list = client.get(f"/instructor/assessments/{asm.public_id}/attempts")
    assert resp_list.status_code == 403

    # 2. Attempt to view attempt details of other instructor's assessment -> 403
    resp_detail = client.get(f"/instructor/attempts/{att.public_id}/results")
    assert resp_detail.status_code == 403


def test_instructor_overview_analytics_has_real_counts(
    client: FlaskClient,
    instructor_a: User,
    course_with_exam: dict[str, Any],
) -> None:
    """Dashboard analytics should return real student and question counts for managed courses."""
    client.post("/auth/login", json={"email": instructor_a.email, "password": "Password@123"})

    resp = client.get("/instructor/dashboard")
    assert resp.status_code == 200
    data = resp.get_json()

    assert data["total_students_count"] >= 1
    assert data["total_questions"] >= 2
    assert data["managed_courses_count"] >= 1
    assert_adr002(data)
