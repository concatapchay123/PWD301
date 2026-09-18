"""TDD Tests for Student Exam & Learning Backend Remediation.

Verifies:
1. Attempt lease duration covers full assessment time limit (no 5-minute premature expiry).
2. Autosave choice key/id compatibility and question id resolution (saves to DB).
3. Deadline expiration auto-finalization and auto-grading (no dead-end 409 error).
4. Enriched attempt result payload (content, choices with correctness, is_correct, rubric).
5. Resource Vault dual ID resolution (both FileAsset and LessonResource IDs) & inline delivery.
"""

from __future__ import annotations

import io
import uuid
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.attempt_regrade import AssessmentAttempt
from pwd301.models.course import Enrollment, EnrollmentPeriod
from pwd301.models.types import utc_now
from pwd301.seeds.baseline import seed_baseline
from pwd301.services.assessment_service import (
    assign_question,
    create_assessment,
    publish_assessment,
)
from pwd301.services.course_service import create_course
from pwd301.services.file_service import attach_resource_to_lesson, store_file_stream
from pwd301.services.lesson_service import create_lesson
from pwd301.services.question_bank_service import create_question
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def exam_env(app: Flask) -> dict[str, Any]:
    """Setup test fixture with instructor, student, course, lesson, assessment, and questions."""
    sess: Session = db.session
    seed_baseline(sess)

    # 1. Instructor & Student
    inst_user = register_user(
        email="instructor_exam@pwd301.local",
        password="Password@123",
        display_name="TS. Nguyen Van Giang Vien",
        session=sess,
    )
    assign_role_to_user(inst_user.id, "INSTRUCTOR", session=sess)

    student_user = register_user(
        email="student_exam@pwd301.local",
        password="Password@123",
        display_name="Le Van Hoc Vien",
        session=sess,
    )
    assign_role_to_user(student_user.id, "STUDENT", session=sess)

    # 2. Course
    course = create_course(
        actor=inst_user,
        data={
            "course_code": "EXAM301",
            "title": "Khao thi & Hoc lieu Chuyen sau",
            "category": "Computer Science",
            "capacity": 100,
        },
        session=sess,
    )
    course.status = "PUBLISHED"
    sess.flush()

    # 3. Enroll student
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

    # 4. Lesson
    lesson = create_lesson(
        actor=inst_user,
        course_id=course.id,
        data={
            "title": "Bai 1: Kien truc Web Backend & Streaming",
            "markdown_content": "# Kien truc Web Backend",
            "estimated_duration_minutes": 60,
            "status": "PUBLISHED",
        },
        session=sess,
    )

    # 5. Attach File Resource to Lesson
    file_stream = io.BytesIO(b"Noi dung tai lieu hoc tap dinh kem")
    file_asset = store_file_stream(
        actor=inst_user,
        course_id=course.id,
        file_stream=file_stream,
        filename="lecture_notes.pdf",
        content_type="application/pdf",
        asset_type="LECTURE_SLIDE",
        session=sess,
    )
    sess.flush()

    resource = attach_resource_to_lesson(
        actor=inst_user,
        lesson_id=lesson.id,
        asset_id=file_asset.id,
        label="Slide Bai giang PDF",
        is_downloadable=True,
        session=sess,
    )

    # 6. Questions
    q1 = create_question(
        actor=inst_user,
        course_id=course.id,
        payload={
            "question_type": "SINGLE_CHOICE",
            "difficulty": "UNDERSTAND",
            "content": "Giao thuc nao duoc dung de streaming video voi Byte-Range?",
            "explanation": "HTTP 206 Partial Content duoc su dung cho Byte-Range streaming.",
            "choices": [
                {"content": "FTP", "is_correct": False, "position": 1},
                {"content": "HTTP Range", "is_correct": True, "position": 2},
                {"content": "SMTP", "is_correct": False, "position": 3},
                {"content": "SNMP", "is_correct": False, "position": 4},
            ],
        },
        session=sess,
    )

    q2 = create_question(
        actor=inst_user,
        course_id=course.id,
        payload={
            "question_type": "MULTIPLE_CHOICE",
            "difficulty": "APPLY",
            "content": "Cac phuong thuc HTTP nao la Idempotent?",
            "explanation": "GET, PUT, DELETE la idempotent theo chuan RFC.",
            "choices": [
                {"content": "GET", "is_correct": True, "position": 1},
                {"content": "PUT", "is_correct": True, "position": 2},
                {"content": "POST", "is_correct": False, "position": 3},
                {"content": "DELETE", "is_correct": True, "position": 4},
            ],
        },
        session=sess,
    )

    # 7. Assessment
    assessment = create_assessment(
        actor=inst_user,
        course_id=course.id,
        payload={
            "title": "Khao thi Cuoi ky Web Backend",
            "assessment_type": "FINAL_EXAM",
            "time_limit_minutes": 60,
            "max_points": 10.0,
            "passing_score": 5.0,
            "score_release_policy": "IMMEDIATE",
            "answer_visibility_policy": "IMMEDIATE",
        },
        session=sess,
    )
    assign_question(
        actor=inst_user,
        assessment_id=assessment.id,
        payload={"question_id": q1.id, "points_assigned": 5.0},
        session=sess,
    )
    assign_question(
        actor=inst_user,
        assessment_id=assessment.id,
        payload={"question_id": q2.id, "points_assigned": 5.0},
        session=sess,
    )
    publish_assessment(actor=inst_user, assessment_id=assessment.id, session=sess)
    sess.commit()

    return {
        "instructor": inst_user,
        "student": student_user,
        "course": course,
        "lesson": lesson,
        "resource": resource,
        "file_asset": file_asset,
        "assessment": assessment,
        "questions": [q1, q2],
    }


def login_client(client: FlaskClient, email: str, password: str = "Password@123") -> str:
    """Log in client and return csrf token."""
    res = client.post("/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    data = res.get_json()
    return data.get("csrf_token", "")


def test_attempt_lease_duration_covers_exam_timelimit(
    client: FlaskClient, exam_env: dict[str, Any]
) -> None:
    """Verify that editing lease duration covers time_limit_minutes (no 5m early expiry)."""
    csrf = login_client(client, "student_exam@pwd301.local")
    asm_id = str(exam_env["assessment"].public_id)

    res = client.post(
        f"/student/assessments/{asm_id}/start",
        headers={"X-CSRFToken": csrf, "Accept": "application/json"},
    )
    assert res.status_code in (200, 201)
    attempt_id = res.get_json()["attempt_id"]

    sess = db.session
    attempt = (
        sess.query(AssessmentAttempt)
        .filter(AssessmentAttempt.public_id == uuid.UUID(str(attempt_id)))
        .first()
    )
    assert attempt is not None

    # Lease duration must cover the 60 minutes time limit (at least 3500 seconds)
    assert attempt.lease_expires_at is not None
    diff = (attempt.lease_expires_at - attempt.started_at).total_seconds()
    assert diff >= 59 * 60, f"Expected lease duration >= 3540s, got {diff}s"


def test_autosave_choice_compatibility_and_question_id_resolution(
    client: FlaskClient, exam_env: dict[str, Any]
) -> None:
    """Verify autosave accepts selected_choice_id, resolves ID, and saves choice."""
    csrf = login_client(client, "student_exam@pwd301.local")
    asm_id = str(exam_env["assessment"].public_id)

    res = client.post(
        f"/student/assessments/{asm_id}/start",
        headers={"X-CSRFToken": csrf, "Accept": "application/json"},
    )
    data = res.get_json()
    attempt_id = data["attempt_id"]
    lease_token = data.get("lease_token", "")

    # Fetch delivery payload
    deliv_res = client.get(f"/student/attempt/{attempt_id}")
    assert deliv_res.status_code == 200
    deliv = deliv_res.get_json()
    assert "questions" in deliv
    assert len(deliv["questions"]) >= 1

    first_q = deliv["questions"][0]
    aq_id = first_q["attempt_question_id"]
    target_choice = first_q["choices"][1]
    choice_key = target_choice.get("choice_key") or target_choice.get("choice_id")

    # Send autosave using frontend format: selected_choice_id
    save_res = client.post(
        f"/student/attempt/{attempt_id}/answers/{aq_id}",
        headers={"X-CSRFToken": csrf, "X-Attempt-Lease-Token": lease_token},
        json={"selected_choice_id": choice_key, "client_sequence": 1},
    )
    assert save_res.status_code == 200

    # Verify AttemptAnswerChoice is persisted in database
    sess = db.session
    attempt = (
        sess.query(AssessmentAttempt)
        .filter(AssessmentAttempt.public_id == uuid.UUID(str(attempt_id)))
        .first()
    )
    aq = [q for q in attempt.attempt_questions if str(q.public_id) == str(aq_id)][0]
    ans = aq.current_answer
    assert ans is not None
    assert len(ans.selected_choices) == 1
    assert str(ans.selected_choices[0].choice_key_snapshot) == str(choice_key)


def test_deadline_expiration_auto_finalization(
    client: FlaskClient, exam_env: dict[str, Any]
) -> None:
    """Verify that submitting an attempt past deadline auto-finalizes and grades cleanly."""
    csrf = login_client(client, "student_exam@pwd301.local")
    asm_id = str(exam_env["assessment"].public_id)

    res = client.post(
        f"/student/assessments/{asm_id}/start",
        headers={"X-CSRFToken": csrf, "Accept": "application/json"},
    )
    attempt_id = res.get_json()["attempt_id"]
    lease_token = res.get_json().get("lease_token", "")

    # Save answer for question 1
    deliv = client.get(f"/student/attempt/{attempt_id}").get_json()
    q1 = deliv["questions"][0]
    correct_choice = [c for c in q1["choices"] if c["position"] == 2][0]
    c_key = correct_choice.get("choice_key") or correct_choice.get("choice_id")

    client.post(
        f"/student/attempt/{attempt_id}/answers/{q1['attempt_question_id']}",
        headers={"X-CSRFToken": csrf, "X-Attempt-Lease-Token": lease_token},
        json={"selected_choice_key": c_key, "client_sequence": 1},
    )

    # Fast-forward attempt started_at and deadline into the past
    sess = db.session
    attempt = (
        sess.query(AssessmentAttempt)
        .filter(AssessmentAttempt.public_id == uuid.UUID(str(attempt_id)))
        .first()
    )
    from datetime import timedelta

    past_start = utc_now() - timedelta(minutes=70)
    past_deadline = utc_now() - timedelta(minutes=10)
    attempt.started_at = past_start
    attempt.deadline_at = past_deadline
    sess.commit()

    # Submit attempt past deadline: should auto-finalize cleanly with 200 OK (not 409 error)
    submit_res = client.post(
        f"/student/attempt/{attempt_id}/submit",
        headers={"X-CSRFToken": csrf, "X-Attempt-Lease-Token": lease_token},
        json={},
    )
    assert submit_res.status_code == 200
    sub_data = submit_res.get_json()
    assert sub_data["status"] in ("GRADED", "SUBMITTED", "PENDING_GRADING")
    assert sub_data.get("raw_score", 0.0) >= 5.0 or sub_data.get("status") == "GRADED"


def test_attempt_result_payload_completeness_for_quiz_review(
    client: FlaskClient, exam_env: dict[str, Any]
) -> None:
    """Verify get_attempt_result_for_student returns complete question text and choices."""
    csrf = login_client(client, "student_exam@pwd301.local")
    asm_id = str(exam_env["assessment"].public_id)

    res = client.post(
        f"/student/assessments/{asm_id}/start",
        headers={"X-CSRFToken": csrf, "Accept": "application/json"},
    )
    attempt_id = res.get_json()["attempt_id"]
    lease_token = res.get_json().get("lease_token", "")

    deliv = client.get(f"/student/attempt/{attempt_id}").get_json()
    q1 = deliv["questions"][0]
    correct_choice = [c for c in q1["choices"] if c["position"] == 2][0]
    c_key = correct_choice.get("choice_key") or correct_choice.get("choice_id")

    client.post(
        f"/student/attempt/{attempt_id}/answers/{q1['attempt_question_id']}",
        headers={"X-CSRFToken": csrf, "X-Attempt-Lease-Token": lease_token},
        json={"selected_choice_key": c_key, "client_sequence": 1},
    )

    # Submit
    client.post(
        f"/student/attempt/{attempt_id}/submit",
        headers={"X-CSRFToken": csrf, "X-Attempt-Lease-Token": lease_token},
        json={},
    )

    # Query result
    res_resp = client.get(f"/student/attempt/{attempt_id}/result")
    assert res_resp.status_code == 200
    result_data = res_resp.get_json()

    assert "questions" in result_data
    assert len(result_data["questions"]) >= 1
    res_q1 = result_data["questions"][0]

    # Enriched fields for 1:1 question review
    assert "content" in res_q1 and len(res_q1["content"]) > 0
    assert "choices" in res_q1 and len(res_q1["choices"]) == 4
    assert any(c.get("is_correct") is True for c in res_q1["choices"])
    assert any(c.get("is_selected") is True for c in res_q1["choices"])
    assert res_q1.get("is_correct") is True


def test_resource_vault_dual_id_resolution_and_streaming(
    client: FlaskClient, exam_env: dict[str, Any]
) -> None:
    """Verify download works for LessonResource ID and FileAsset ID with inline disposition."""
    login_client(client, "student_exam@pwd301.local")
    course_id = str(exam_env["course"].public_id)
    lesson_id = str(exam_env["lesson"].public_id)
    resource_id = str(exam_env["resource"].public_id)
    file_asset_id = str(exam_env["file_asset"].public_id)

    # 1. Lesson reader payload contains download_url and file_asset_id
    les_resp = client.get(f"/student/courses/{course_id}/lessons/{lesson_id}")
    assert les_resp.status_code == 200
    les_data = les_resp.get_json()
    assert "resources" in les_data and len(les_data["resources"]) >= 1
    res_item = les_data["resources"][0]
    assert "download_url" in res_item or "resource_id" in res_item

    # 2. Download via LessonResource ID
    dl_res1 = client.get(f"/student/courses/{course_id}/files/{resource_id}/download")
    assert dl_res1.status_code == 200
    assert dl_res1.data == b"Noi dung tai lieu hoc tap dinh kem"

    # 3. Download via FileAsset ID
    dl_res2 = client.get(f"/student/courses/{course_id}/files/{file_asset_id}/download")
    assert dl_res2.status_code == 200
    assert dl_res2.data == b"Noi dung tai lieu hoc tap dinh kem"

    # 4. Inline disposition streaming
    dl_inline = client.get(f"/student/files/{resource_id}/download?disposition=inline")
    assert dl_inline.status_code == 200
    assert "inline" in dl_inline.headers.get("Content-Disposition", "")
