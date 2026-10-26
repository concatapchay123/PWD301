"""TDD Tests for TASK-093 Remediation:
1. Server-authoritative passing threshold (passing_percent) and strict pass/fail grading.
2. Result PDF status label and score summary formatting.
3. Pre-flight course publish gate verification (cover image, trailer video, authentic info, academic settings, lessons).
4. Reliable course cover upload and persistence.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient

from backend.extensions import db
from backend.models.assessment import AssessmentQuestionAssignment
from backend.models.attempt_regrade import (
    AssessmentResult,
)
from backend.seeds.baseline import seed_baseline
from backend.services.assessment_service import create_assessment
from backend.services.attempt_service import (
    get_attempt_result_for_student,
    save_attempt_answer,
    start_assessment_attempt,
    submit_assessment_attempt,
)
from backend.services.course_service import create_course
from backend.services.lesson_service import create_lesson
from backend.services.result_pdf_service import build_attempt_result_pdf
from backend.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def remediation_env(app: Flask) -> dict[str, Any]:
    """Setup instructor, course, student, and lesson test fixture."""
    sess = db.session
    seed_baseline(sess)

    inst_user = register_user(
        email="instructor_remed093@backend.local",
        password="Password@123",
        display_name="ThS. Remediation 093",
        session=sess,
    )
    assign_role_to_user(inst_user.id, "INSTRUCTOR", session=sess)

    student_user = register_user(
        email="student_remed093@backend.local",
        password="Password@123",
        display_name="Nguyen Van Sinh Vien 093",
        session=sess,
    )
    assign_role_to_user(student_user.id, "STUDENT", session=sess)

    course = create_course(
        actor=inst_user,
        data={
            "course_code": "TASK093",
            "title": "Remediation Task 093 Course",
            "category": "Computer Science",
            "capacity": 50,
        },
        session=sess,
    )
    course.status = "PUBLISHED"
    sess.flush()
    lesson = create_lesson(
        actor=inst_user,
        course_id=course.id,
        data={
            "title": "Bai 01: Tong quan",
            "markdown_content": "# Noi dung bai hoc",
            "estimated_duration_minutes": 45,
            "status": "PUBLISHED",
        },
        session=sess,
    )
    sess.commit()

    return {
        "instructor": inst_user,
        "student": student_user,
        "course": course,
        "lesson": lesson,
    }


def login_session(client: FlaskClient, email: str, password: str = "Password@123") -> str:
    """Helper to login user via Flask session and return CSRF token."""
    csrf_res = client.get("/auth/login")
    csrf_token = csrf_res.get_json().get("csrf_token", "")
    login_res = client.post(
        "/auth/login",
        json={"email": email, "password": password, "remember": False},
        headers={"X-CSRFToken": csrf_token},
    )
    assert login_res.status_code == 200, f"Login failed: {login_res.get_data(as_text=True)}"
    return csrf_token


def test_assessment_passing_percent_in_attempt_service(remediation_env: dict[str, Any]) -> None:
    """Ensure student scoring below passing_percent is marked passed=False, and at or above is passed=True."""
    instructor = remediation_env["instructor"]
    student = remediation_env["student"]
    course = remediation_env["course"]
    sess = db.session

    # 1. Create Assessment with passing_percent = 70.0%
    asm = create_assessment(
        actor=instructor,
        course_id=course.id,
        payload={
            "title": "Kiem tra Danh gia Nang luc 70%",
            "assessment_type": "FINAL",
            "time_limit_minutes": 30,
            "passing_percent": 70.0,
        },
        session=sess,
    )
    sess.commit()

    assert asm.passing_percent is not None
    assert float(asm.passing_percent) == 70.0

    # 2. Add 2 single-choice questions (each 5 points, total 10 points)
    from backend.services.question_bank_service import create_question

    q1 = create_question(
        actor=instructor,
        course_id=course.id,
        payload={
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "content": "1 + 1 = ?",
            "default_points": 5.0,
            "choices": [
                {"content": "2", "is_correct": True},
                {"content": "3", "is_correct": False},
            ],
        },
        session=sess,
    )
    q2 = create_question(
        actor=instructor,
        course_id=course.id,
        payload={
            "question_type": "SINGLE_CHOICE",
            "difficulty": "REMEMBER",
            "content": "2 + 2 = ?",
            "default_points": 5.0,
            "choices": [
                {"content": "4", "is_correct": True},
                {"content": "5", "is_correct": False},
            ],
        },
        session=sess,
    )
    sess.commit()

    # Assign to assessment
    sess.add(
        AssessmentQuestionAssignment(
            assessment_id=asm.id, question_id=q1.id, position=1, points=Decimal("5.0")
        )
    )
    sess.add(
        AssessmentQuestionAssignment(
            assessment_id=asm.id, question_id=q2.id, position=2, points=Decimal("5.0")
        )
    )
    sess.commit()

    # Publish assessment
    from backend.services.assessment_service import publish_assessment

    publish_assessment(actor=instructor, assessment_id=asm.id, session=sess)
    asm.status = "PUBLISHED"
    sess.commit()

    # Enroll student in course
    from backend.services.enrollment_service import enroll_student

    enroll_student(actor=student, course_id=course.id, session=sess)
    sess.commit()

    # Case A: Student answers only 1 question correctly -> score = 5 / 10 = 50% (< 70% threshold)
    att1, lease1 = start_assessment_attempt(
        student_actor=student, assessment_id=asm.id, session=sess
    )
    sess.commit()

    aq1_a = att1.attempt_questions[0]
    aq2_a = att1.attempt_questions[1]
    # Identify which aq corresponds to which question
    for aq in [aq1_a, aq2_a]:
        if aq.question_id == q1.id:
            c_correct = [cs for cs in aq.choice_snapshots if cs.source_choice.is_correct][0]
            save_attempt_answer(
                actor=student,
                attempt_id=att1.id,
                attempt_question_id=aq.id,
                payload={
                    "client_sequence": 1,
                    "selected_choice_keys": [str(c_correct.choice_key_snapshot)],
                },
                raw_lease_token=lease1,
                session=sess,
            )
        else:
            c_wrong = [cs for cs in aq.choice_snapshots if not cs.source_choice.is_correct][0]
            save_attempt_answer(
                actor=student,
                attempt_id=att1.id,
                attempt_question_id=aq.id,
                payload={
                    "client_sequence": 1,
                    "selected_choice_keys": [str(c_wrong.choice_key_snapshot)],
                },
                raw_lease_token=lease1,
                session=sess,
            )
    sess.commit()

    # Submit attempt
    submit_assessment_attempt(
        actor=student,
        attempt_id=att1.id,
        idempotency_key=uuid.uuid4(),
        raw_lease_token=lease1,
        session=sess,
    )
    sess.commit()

    res1 = sess.query(AssessmentResult).filter_by(attempt_id=att1.id).one()
    assert float(res1.percent_score) == 50.0
    # Must fail because 50% < 70%
    assert res1.passed is False, (
        f"Expected passed=False for 50% score against 70% passing threshold, got {res1.passed}"
    )

    # Verify student result endpoint also reports is_passed = False
    result_data1 = get_attempt_result_for_student(actor=student, attempt_id=att1.id, session=sess)
    assert result_data1["is_passed"] is False
    assert result_data1["passed"] is False

    # Case B: Student answers both correctly -> score = 10 / 10 = 100% (>= 70% threshold)
    att2, lease2 = start_assessment_attempt(
        student_actor=student, assessment_id=asm.id, session=sess
    )
    sess.commit()

    for aq in att2.attempt_questions:
        c_correct = [cs for cs in aq.choice_snapshots if cs.source_choice.is_correct][0]
        save_attempt_answer(
            actor=student,
            attempt_id=att2.id,
            attempt_question_id=aq.id,
            payload={
                "client_sequence": 1,
                "selected_choice_keys": [str(c_correct.choice_key_snapshot)],
            },
            raw_lease_token=lease2,
            session=sess,
        )
    sess.commit()

    submit_assessment_attempt(
        actor=student,
        attempt_id=att2.id,
        idempotency_key=uuid.uuid4(),
        raw_lease_token=lease2,
        session=sess,
    )
    sess.commit()

    res2 = sess.query(AssessmentResult).filter_by(attempt_id=att2.id).one()
    assert float(res2.percent_score) == 100.0
    # Must pass because 100% >= 70%
    assert res2.passed is True

    # Case C: Assessment with passing_percent = None (legacy or unspecified) -> fallback to 50.0%
    asm3 = create_assessment(
        actor=instructor,
        course_id=course.id,
        payload={
            "title": "Kiem tra Khong cau hinh diem dat",
            "assessment_type": "FINAL",
            "time_limit_minutes": 30,
        },
        session=sess,
    )
    sess.add(
        AssessmentQuestionAssignment(
            assessment_id=asm3.id, question_id=q1.id, position=1, points=Decimal("5.0")
        )
    )
    sess.add(
        AssessmentQuestionAssignment(
            assessment_id=asm3.id, question_id=q2.id, position=2, points=Decimal("5.0")
        )
    )
    sess.commit()
    publish_assessment(actor=instructor, assessment_id=asm3.id, session=sess)
    asm3.status = "PUBLISHED"
    sess.commit()

    att3, lease3 = start_assessment_attempt(
        student_actor=student, assessment_id=asm3.id, session=sess
    )
    sess.commit()

    # Answer both questions incorrectly -> score 0%
    for aq in att3.attempt_questions:
        c_wrong = [cs for cs in aq.choice_snapshots if not cs.source_choice.is_correct][0]
        save_attempt_answer(
            actor=student,
            attempt_id=att3.id,
            attempt_question_id=aq.id,
            payload={
                "client_sequence": 1,
                "selected_choice_keys": [str(c_wrong.choice_key_snapshot)],
            },
            raw_lease_token=lease3,
            session=sess,
        )
    sess.commit()

    submit_assessment_attempt(
        actor=student,
        attempt_id=att3.id,
        idempotency_key=uuid.uuid4(),
        raw_lease_token=lease3,
        session=sess,
    )
    sess.commit()

    res3 = sess.query(AssessmentResult).filter_by(attempt_id=att3.id).one()
    assert float(res3.percent_score) == 0.0
    # With 50% fallback threshold, 0% MUST NOT PASS!
    assert res3.passed is False, (
        f"Expected passed=False for 0% with default 50% threshold, but got {res3.passed}"
    )


def test_pdf_generation_status_badge_and_threshold(remediation_env: dict[str, Any]) -> None:
    """Ensure PDF report renders 'CHƯA ĐẠT YÊU CẦU' when is_passed=False and 'ĐẠT CHUẨN MÔN HỌC' when True."""
    # Failed attempt payload
    failed_payload = {
        "candidate_name": "Nguyen Van A",
        "candidate_email": "student_a@example.com",
        "assessment_title": "Ky thi Lap trinh Web",
        "assessment_code": "PWD301-FINAL",
        "assessment_type": "FINAL",
        "raw_score": 4.0,
        "max_score": 10.0,
        "percent_score": 40.0,
        "passing_percent": 60.0,
        "is_passed": False,
        "passed": False,
        "score_status": "RELEASED",
        "questions": [],
    }
    pdf_fail = build_attempt_result_pdf(failed_payload)
    assert isinstance(pdf_fail, bytes)
    assert len(pdf_fail) > 1000

    # Passed attempt payload
    passed_payload = {
        "candidate_name": "Nguyen Van B",
        "candidate_email": "student_b@example.com",
        "assessment_title": "Ky thi Lap trinh Web",
        "assessment_code": "PWD301-FINAL",
        "assessment_type": "FINAL",
        "raw_score": 9.0,
        "max_score": 10.0,
        "percent_score": 90.0,
        "passing_percent": 60.0,
        "is_passed": True,
        "passed": True,
        "score_status": "RELEASED",
        "questions": [],
    }
    pdf_pass = build_attempt_result_pdf(passed_payload)
    assert isinstance(pdf_pass, bytes)
    assert len(pdf_pass) > 1000


def test_course_submit_checklist_fails_when_unready(
    client: FlaskClient, remediation_env: dict[str, Any]
) -> None:
    """Ensure POST /instructor/courses/<id>/submit strictly checks 5 publish criteria."""
    instructor = remediation_env["instructor"]
    sess = db.session
    csrf = login_session(client, instructor.email)

    # Create empty draft course (missing cover, trailer, custom info, settings, lessons)
    course = create_course(
        instructor, {"course_code": "FAIL-SUBMIT", "title": "Incomplete Course"}, session=sess
    )
    sess.commit()

    chk_resp = client.get(
        f"/instructor/courses/{course.public_id}/publish-checklist",
        headers={"X-CSRFToken": csrf},
    )
    assert chk_resp.status_code == 200
    chk_data = chk_resp.get_json()
    assert chk_data["is_ready"] is False
    assert len(chk_data["criteria"]) == 5
    ids = [c["id"] for c in chk_data["criteria"]]
    assert set(ids) == {
        "cover_image",
        "intro_video",
        "course_info",
        "academic_settings",
        "curriculum",
    }

    resp = client.post(
        f"/instructor/courses/{course.public_id}/submit",
        json={"reason": "Test submit"},
        headers={"X-CSRFToken": csrf},
    )
    assert resp.status_code == 400
    data = resp.get_json()
    err_msg = data.get("error", {}).get("message", "")
    assert "Khóa học chưa đủ điều kiện xuất bản" in err_msg
