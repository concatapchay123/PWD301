"""Tests for Assessment Engine Fixes: Aliases, Invariants, and Instructor Web Flow."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient

from pwd301.extensions import db
from pwd301.models.course import Course
from pwd301.models.identity import Role
from pwd301.services.assessment_service import (
    assign_question,
    create_assessment,
    publish_assessment,
    update_assessment,
)
from pwd301.services.course_service import create_course
from pwd301.services.exceptions import AssessmentLockedError, AssessmentValidationError
from pwd301.services.question_bank_service import create_question
from pwd301.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user


@pytest.fixture
def setup_data(app: Flask) -> dict[str, Any]:
    sess = db.session
    for code, name in [("STUDENT", "Student"), ("INSTRUCTOR", "Instructor"), ("ADMIN", "Admin")]:
        r = sess.query(Role).filter_by(code=code).first()
        if not r:
            sess.add(Role(code=code, name=name))
    sess.commit()

    instructor = register_user(
        email=f"inst_{datetime.now(UTC).timestamp()}@fpt.edu.vn",
        password="ValidPassword123!",
        display_name="Instructor Testing",
        session=sess,
    )
    assign_role_to_user(instructor.id, "INSTRUCTOR", session=sess)

    course = create_course(
        instructor,
        {
            "course_code": f"ASM{int(datetime.now(UTC).timestamp()) % 10000}",
            "title": "Assessment Engine Architecture Course",
            "summary": "Testing assessment fixes",
        },
        session=sess,
    )
    sess.commit()

    q1 = create_question(
        instructor,
        course.id,
        {
            "content": "What is 2 + 2?",
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "default_points": 2.0,
            "choices": [
                {"content": "3", "is_correct": False, "position": 1},
                {"content": "4", "is_correct": True, "position": 2},
            ],
            "provenance": {"source_type": "MANUAL"},
        },
        session=sess,
    )
    sess.commit()

    return {"instructor": instructor, "course": course, "question": q1}


def test_assessment_type_and_field_aliases(app: Flask, setup_data: dict[str, Any]):
    """Verify alias mapping for EXAM, FINAL_EXAM, PRACTICE_QUIZ, and field aliases."""
    instructor = setup_data["instructor"]
    course = setup_data["course"]

    # 1. EXAM -> MIDTERM, duration_minutes -> time_limit, max_attempts -> attempt_limit
    asm1 = create_assessment(
        actor=instructor,
        course_id=course.id,
        payload={
            "title": "Midterm Exam with Aliases",
            "assessment_type": "EXAM",
            "duration_minutes": 60,
            "max_attempts": 2,
            "is_randomized": True,
            "passing_score": 60,
        },
        session=db.session,
    )
    assert asm1.assessment_type == "MIDTERM"
    assert asm1.time_limit_minutes == 60
    assert asm1.attempt_limit == 2
    assert asm1.shuffle_questions is True
    assert asm1.shuffle_choices is True
    assert asm1.passing_percent == Decimal("60")

    # 2. FINAL_EXAM -> FINAL
    asm2 = create_assessment(
        actor=instructor,
        course_id=course.id,
        payload={
            "title": "Final Exam",
            "assessment_type": "FINAL_EXAM",
        },
        session=db.session,
    )
    assert asm2.assessment_type == "FINAL"

    # 3. PRACTICE_QUIZ & ASSIGNMENT -> PRACTICE
    asm3 = create_assessment(
        actor=instructor,
        course_id=course.id,
        payload={
            "title": "Practice Quiz",
            "assessment_type": "PRACTICE_QUIZ",
        },
        session=db.session,
    )
    assert asm3.assessment_type == "PRACTICE"

    asm4 = create_assessment(
        actor=instructor,
        course_id=course.id,
        payload={
            "title": "Assignment Practice",
            "assessment_type": "ASSIGNMENT",
        },
        session=db.session,
    )
    assert asm4.assessment_type == "PRACTICE"


def test_assessment_timing_window_validation(app: Flask, setup_data: dict[str, Any]):
    """Verify BR-028: duration_minutes <= (close_at - open_at)."""
    instructor = setup_data["instructor"]
    course = setup_data["course"]

    now = datetime.now(UTC)
    open_dt = now + timedelta(days=1)
    close_dt = open_dt + timedelta(minutes=30)  # 30-minute window

    # 1. 45-minute duration in a 30-minute window must fail
    with pytest.raises(
        AssessmentValidationError, match="cannot exceed the open/close window duration"
    ):
        create_assessment(
            actor=instructor,
            course_id=course.id,
            payload={
                "title": "Window Overflow Exam",
                "assessment_type": "QUIZ",
                "open_at": open_dt.isoformat(),
                "close_at": close_dt.isoformat(),
                "duration_minutes": 45,
            },
            session=db.session,
        )

    # 2. 25-minute duration in a 30-minute window must pass
    valid_asm = create_assessment(
        actor=instructor,
        course_id=course.id,
        payload={
            "title": "Valid Window Exam",
            "assessment_type": "QUIZ",
            "open_at": open_dt.isoformat(),
            "close_at": close_dt.isoformat(),
            "duration_minutes": 25,
        },
        session=db.session,
    )
    assert valid_asm.id is not None
    assert valid_asm.time_limit_minutes == 25


def test_timing_lock_invariant(app: Flask, setup_data: dict[str, Any]):
    """Verify BR-031: Timing Lock after PUBLISHED status."""
    instructor = setup_data["instructor"]
    course = setup_data["course"]
    q1 = setup_data["question"]

    asm = create_assessment(
        actor=instructor,
        course_id=course.id,
        payload={
            "title": "Lock Testing Exam",
            "assessment_type": "MIDTERM",
            "time_limit_minutes": 45,
            "attempt_limit": 1,
        },
        session=db.session,
    )

    # Assign question so it can be published
    assign_question(
        actor=instructor,
        assessment_id=asm.id,
        payload={"question_id": str(q1.public_id), "points": 10.0},
        session=db.session,
    )

    # Publish
    publish_assessment(actor=instructor, assessment_id=asm.id, session=db.session)
    assert asm.status == "PUBLISHED"

    # Attempt to change time limit while published must fail
    with pytest.raises(AssessmentLockedError, match="time_limit_minutes.*is locked after publish"):
        update_assessment(
            actor=instructor,
            assessment_id=asm.id,
            payload={"time_limit_minutes": 60},
            session=db.session,
        )


def test_instructor_web_flow_and_builder(client: FlaskClient, setup_data: dict[str, Any]):
    """Verify Instructor Web UI flow for creating and managing assessments."""
    instructor = setup_data["instructor"]
    course = setup_data["course"]
    q1 = setup_data["question"]

    # Log in instructor via Flask session
    login_web_user(client, instructor)
    with client.session_transaction() as sess:
        sess["active_role"] = "INSTRUCTOR"

    # 1. POST HTML form to create assessment with alias EXAM
    resp = client.post(
        f"/instructor/courses/{course.public_id}/assessments",
        data={
            "title": "Web Created Exam",
            "assessment_type": "EXAM",
            "time_limit_minutes": "45",
            "passing_percent": "50",
            "attempt_limit": "1",
            "score_release_policy": "IMMEDIATE",
        },
        headers={"Accept": "text/html"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert "Đã tạo bài kiểm tra" in resp.text
    assert "Web Created Exam" in resp.text

    # Verify assessment exists in DB
    asm = db.session.query(Course).filter_by(public_id=course.public_id).first().assessments[0]
    assert asm.assessment_type == "MIDTERM"

    # 2. GET Assessment Builder page in HTML
    builder_resp = client.get(
        f"/instructor/assessments/{asm.public_id}",
        headers={"Accept": "text/html"},
    )
    assert builder_resp.status_code == 200
    assert "Cấu hình Đề thi: Web Created Exam" in builder_resp.text
    assert "Thông số & Thời lượng" in builder_resp.text
    assert "Chấm lại & Đính chính" in builder_resp.text

    # 3. Assign question via HTML form
    assign_resp = client.post(
        f"/instructor/assessments/{asm.public_id}/questions",
        data={
            "question_id": str(q1.public_id),
            "points": "5.0",
        },
        headers={"Accept": "text/html"},
        follow_redirects=True,
    )
    assert assign_resp.status_code == 200
    assert "Đã gán câu hỏi vào đề thi thành công!" in assign_resp.text
    assert "What is 2 + 2?" in assign_resp.text

    # 4. Publish assessment via HTML form
    pub_resp = client.post(
        f"/instructor/assessments/{asm.public_id}/publish",
        headers={"Accept": "text/html"},
        follow_redirects=True,
    )
    assert pub_resp.status_code == 200
    assert "Đã xuất bản bài thi" in pub_resp.text
    assert "ĐÃ XUẤT BẢN (PUBLISHED)" in pub_resp.text
    assert "Khóa Thời gian đang kích hoạt" in pub_resp.text
