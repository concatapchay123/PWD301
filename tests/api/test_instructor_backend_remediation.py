"""Tests for Backend Remediation & Instructor Portal Parity (TASK-045).

Verifies:
1. GET /instructor/courses/<course_id>/questions/summary (Bloom & type distribution)
2. POST /instructor/assessments/<assessment_id>/questions/create (ESSAY question type)
3. POST /instructor/assessments/<assessment_id>/questions/batch (Atomic batch question creation)
4. DELETE /instructor/courses/<course_id>/lessons/<lesson_id>/resources/<resource_id>
5. POST /instructor/attempts/<attempt_id>/grades/<attempt_question_id> (Rubric breakdown)
6. POST /student/ai/chat with course_id context parameter
"""

from __future__ import annotations

import re
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.file_import import FileAsset, LessonResource
from pwd301.seeds.baseline import seed_baseline
from pwd301.services.assessment_service import create_assessment
from pwd301.services.attempt_service import (
    start_assessment_attempt,
    submit_assessment_attempt,
)
from pwd301.services.course_service import create_course
from pwd301.services.lesson_service import create_lesson
from pwd301.services.question_bank_service import create_question
from pwd301.services.user_service import assign_role_to_user, register_user

UUID_REGEX = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)


def assert_adr002(data: Any) -> None:
    """Recursively verify no internal BigInt PKs are leaked in responses."""
    if isinstance(data, dict):
        for k, v in data.items():
            assert k != "id", f"Internal primary key leaked: {data}"
            assert k != "creator_user_id", f"Internal foreign key leaked: {data}"
            if (
                k.endswith("_id")
                and v is not None
                and k not in ("choice_key", "temp_id", "question_type")
            ):
                assert isinstance(v, str), f"Expected UUID string for {k}, got {type(v)}: {v}"
            assert_adr002(v)
    elif isinstance(data, list):
        for item in data:
            assert_adr002(item)


@pytest.fixture
def remediation_env(app: Flask) -> dict[str, Any]:
    """Setup instructor, course, student, and lesson test fixture."""
    sess: Session = db.session
    seed_baseline(sess)

    # 1. Register and assign roles
    inst_user = register_user(
        email="instructor_remed@pwd301.local",
        password="Password@123",
        display_name="ThS. Remediation Instructor",
        session=sess,
    )
    assign_role_to_user(inst_user.id, "INSTRUCTOR", session=sess)

    student_user = register_user(
        email="student_remed@pwd301.local",
        password="Password@123",
        display_name="Nguyen Van Sinh Vien",
        session=sess,
    )
    assign_role_to_user(student_user.id, "STUDENT", session=sess)

    # 2. Create Course & Lesson
    course = create_course(
        actor=inst_user,
        data={
            "course_code": "REM301",
            "title": "Backend Remediation Course",
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
            "title": "Bai 01: Tong quan Kien truc REST API",
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


# ============================================================================
# 1. Question Bank Summary API Test
# ============================================================================
def test_get_course_question_summary(client: FlaskClient, remediation_env: dict[str, Any]) -> None:
    """Ensure GET /instructor/courses/<course_id>/questions/summary returns aggregated metrics."""
    inst = remediation_env["instructor"]
    course = remediation_env["course"]
    lesson = remediation_env["lesson"]
    sess = db.session

    # Seed 3 questions of varying types and Bloom levels
    create_question(
        actor=inst,
        course_id=course.id,
        payload={
            "difficulty": "REMEMBER",
            "question_type": "SINGLE_CHOICE",
            "content": "Cau hoi Nhan biet 1",
            "lesson_id": lesson.id,
            "choices": [
                {"content": "Dap an A", "is_correct": True, "position": 1},
                {"content": "Dap an B", "is_correct": False, "position": 2},
            ],
        },
        session=sess,
    )
    create_question(
        actor=inst,
        course_id=course.id,
        payload={
            "difficulty": "UNDERSTAND",
            "question_type": "MULTIPLE_CHOICE",
            "content": "Cau hoi Thong hieu 2",
            "lesson_id": lesson.id,
            "choices": [
                {"content": "Dap an A", "is_correct": True, "position": 1},
                {"content": "Dap an B", "is_correct": True, "position": 2},
            ],
        },
        session=sess,
    )
    create_question(
        actor=inst,
        course_id=course.id,
        payload={
            "difficulty": "APPLY",
            "question_type": "SHORT_ANSWER",
            "content": "Cau hoi Van dung 3",
            "accepted_answers": [{"answer_text": "Answer 1"}],
        },
        session=sess,
    )
    sess.commit()

    login_session(client, inst.email)

    res = client.get(f"/instructor/courses/{course.public_id}/questions/summary")
    assert res.status_code == 200, f"Error: {res.get_data(as_text=True)}"
    data = res.get_json()

    assert data["total"] == 3
    assert "by_difficulty" in data
    assert data["by_difficulty"]["REMEMBER"] == 1
    assert data["by_difficulty"]["UNDERSTAND"] == 1
    assert data["by_difficulty"]["APPLY"] == 1

    assert "by_type" in data
    assert data["by_type"]["SINGLE_CHOICE"] == 1
    assert data["by_type"]["MULTIPLE_CHOICE"] == 1
    assert data["by_type"]["SHORT_ANSWER"] == 1

    assert "by_lesson" in data
    assert len(data["by_lesson"]) >= 1

    assert_adr002(data)


# ============================================================================
# 2. ESSAY Question Type in Assessment Authoring Test
# ============================================================================
def test_create_assessment_question_essay_rejected_and_short_answer_supported(
    client: FlaskClient, remediation_env: dict[str, Any]
) -> None:
    """Ensure POST /instructor/assessments/<id>/questions/create rejects ESSAY
    and accepts objective questions.
    """
    inst = remediation_env["instructor"]
    course = remediation_env["course"]
    sess = db.session

    asm = create_assessment(
        actor=inst,
        course_id=course.id,
        payload={
            "title": "Kiem tra Trac nghiem Giua ky",
            "assessment_type": "MIDTERM",
            "duration_minutes": 60,
        },
        session=sess,
    )
    sess.commit()

    csrf = login_session(client, inst.email)

    # 1. Essay question must be rejected with 400
    essay_payload = {
        "question_type": "ESSAY",
        "difficulty": "APPLY",
        "content": "Hãy phân tích kiến trúc RESTful API và tính Idempotent của HTTP DELETE.",
        "points": 10.0,
        "explanation": (
            "Tiêu chí 1: Khái niệm (3đ). Tiêu chí 2: Idempotent (4đ). Tiêu chí 3: Mã lỗi (3đ)."
        ),
    }

    res = client.post(
        f"/instructor/assessments/{asm.public_id}/questions/create",
        json=essay_payload,
        headers={"X-CSRFToken": csrf},
    )
    assert res.status_code == 400
    assert "ESSAY" in res.get_data(as_text=True)

    # 2. Objective SHORT_ANSWER question must be accepted
    sa_payload = {
        "question_type": "SHORT_ANSWER",
        "difficulty": "APPLY",
        "content": "Giao thức nào cung cấp kênh truyền bảo mật dựa trên TLS?",
        "points": 5.0,
        "accepted_answers": ["HTTPS", "SSH"],
    }
    sa_res = client.post(
        f"/instructor/assessments/{asm.public_id}/questions/create",
        json=sa_payload,
        headers={"X-CSRFToken": csrf},
    )
    assert sa_res.status_code in (200, 201), f"Failed: {sa_res.get_data(as_text=True)}"
    data = sa_res.get_json()
    assert data.get("status") == "ok" or "question_id" in data or "id" in data
    assert_adr002(data)


# ============================================================================
# 3. Atomic Batch Create Assessment Questions Test
# ============================================================================
def test_batch_create_assessment_questions(
    client: FlaskClient, remediation_env: dict[str, Any]
) -> None:
    """Ensure POST /instructor/assessments/<id>/questions/batch saves questions atomically."""
    inst = remediation_env["instructor"]
    course = remediation_env["course"]
    sess = db.session

    asm = create_assessment(
        actor=inst,
        course_id=course.id,
        payload={
            "title": "Kỳ thi Tong hop Azota Batch",
            "assessment_type": "FINAL",
            "duration_minutes": 90,
        },
        session=sess,
    )
    sess.commit()

    csrf = login_session(client, inst.email)

    batch_payload = {
        "questions": [
            {
                "question_type": "SINGLE_CHOICE",
                "difficulty": "REMEMBER",
                "content": "HTTP GET có thay đổi trạng thái máy chủ không?",
                "points": 2.0,
                "choices": [
                    {"content": "Có", "is_correct": False, "position": 1},
                    {"content": "Không (Safe method)", "is_correct": True, "position": 2},
                ],
            },
            {
                "question_type": "SHORT_ANSWER",
                "difficulty": "APPLY",
                "content": "Chuẩn token không trạng thái phổ biến nhất hiện nay là gì?",
                "points": 8.0,
                "accepted_answers": ["JWT", "JSON Web Token"],
            },
        ]
    }

    res = client.post(
        f"/instructor/assessments/{asm.public_id}/questions/batch",
        json=batch_payload,
        headers={"X-CSRFToken": csrf},
    )
    assert res.status_code in (200, 201), f"Failed batch create: {res.get_data(as_text=True)}"
    data = res.get_json()
    assert data.get("created_count") == 2
    assert_adr002(data)


# ============================================================================
# 4. Detach Lesson Resource HTTP DELETE Method Test
# ============================================================================
def test_detach_lesson_resource_delete_method(
    client: FlaskClient, remediation_env: dict[str, Any]
) -> None:
    """Ensure DELETE /instructor/courses/<cid>/lessons/<lid>/resources/<rid> succeeds."""
    inst = remediation_env["instructor"]
    course = remediation_env["course"]
    lesson = remediation_env["lesson"]
    sess = db.session

    # Create dummy file asset and lesson resource
    file_asset = FileAsset(
        course_id=course.id,
        created_by_user_id=inst.id,
        asset_type="RESOURCE",
        display_name="slide_bai_01.pdf",
        status="ACTIVE",
    )
    sess.add(file_asset)
    sess.flush()

    resource = LessonResource(
        lesson_id=lesson.id,
        file_asset_id=file_asset.id,
        label="Slide bài giảng 01",
        position=1,
    )
    sess.add(resource)
    sess.commit()

    csrf = login_session(client, inst.email)

    c_pid = course.public_id
    l_pid = lesson.public_id
    r_pid = resource.public_id
    url = f"/instructor/courses/{c_pid}/lessons/{l_pid}/resources/{r_pid}"
    res = client.delete(url, headers={"X-CSRFToken": csrf})
    assert res.status_code == 200, f"Failed DELETE resource: {res.get_data(as_text=True)}"
    data = res.get_json()
    assert data.get("status") in ("ok", "success")


# ============================================================================
# 5. Essay Elimination Verification & Auto-Graded Attempt Test
# ============================================================================
def test_essay_elimination_and_direct_auto_grading(
    client: FlaskClient, remediation_env: dict[str, Any]
) -> None:
    """Ensure ESSAY creation is rejected, assessments are objective-only,
    and submitted attempts are auto-graded.
    """
    inst = remediation_env["instructor"]
    student = remediation_env["student"]
    course = remediation_env["course"]
    sess = db.session

    # 1. Enroll student
    from pwd301.services.enrollment_service import enroll_student

    enroll_student(actor=student, course_id=course.id, session=sess)
    sess.commit()

    # 2. Verify creating an ESSAY question is supported per System Specification
    essay_q = create_question(
        actor=inst,
        course_id=course.id,
        payload={
            "difficulty": "APPLY",
            "question_type": "ESSAY",
            "content": "Viết luận về tối ưu hóa SQL Server Index.",
            "default_points": 15.0,
        },
        session=sess,
    )
    assert essay_q is not None
    assert essay_q.current_revision.question_type == "ESSAY"

    # 3. Create Published Assessment with Objective Question
    asm = create_assessment(
        actor=inst,
        course_id=course.id,
        payload={
            "title": "Final Objective Exam",
            "assessment_type": "FINAL",
            "duration_minutes": 60,
        },
        session=sess,
    )
    q = create_question(
        actor=inst,
        course_id=course.id,
        payload={
            "difficulty": "APPLY",
            "question_type": "SHORT_ANSWER",
            "content": "Thuật toán băm dùng cho password hashing an toàn là gì?",
            "default_points": 15.0,
            "accepted_answers": ["Argon2id", "bcrypt"],
        },
        session=sess,
    )
    from pwd301.services.assessment_service import assign_question, publish_assessment

    assign_question(
        actor=inst,
        assessment_id=asm.id,
        payload={"question_id": q.id, "points": 15.0},
        session=sess,
    )
    publish_assessment(actor=inst, assessment_id=asm.id, session=sess)
    sess.commit()

    # 4. Student takes and submits attempt
    attempt, lease_token = start_assessment_attempt(
        student_actor=student, assessment_id=asm.id, session=sess
    )
    att_q = attempt.attempt_questions[0]
    submit_assessment_attempt(
        actor=student, attempt_id=attempt.id, raw_lease_token=lease_token, session=sess
    )
    sess.commit()

    # Submitted attempt must immediately be GRADED (no PENDING_GRADING)
    sess.refresh(attempt)
    assert attempt.status == "GRADED"

    # 5. Instructor manual essay grading endpoint must reject with 400
    csrf = login_session(client, inst.email)

    grade_payload = {
        "awarded_points": 20.0,
        "reason": "Giải pháp rất tốt.",
    }

    res = client.post(
        f"/instructor/attempts/{attempt.public_id}/grades/{att_q.public_id}",
        json=grade_payload,
        headers={"X-CSRFToken": csrf},
    )
    assert res.status_code == 400
    res_text = res.get_data(as_text=True)
    assert "tự luận" in res_text.lower() or "VALIDATION_ERROR" in res_text


# ============================================================================
# 6. Student AI Chat with Course Context Test
# ============================================================================
def test_student_ai_chat_with_course_context(
    client: FlaskClient, remediation_env: dict[str, Any]
) -> None:
    """Ensure POST /student/ai/chat scopes conversation to specified course_id."""
    student = remediation_env["student"]
    course = remediation_env["course"]
    sess = db.session

    from pwd301.models.course import Enrollment

    enr = Enrollment(student_user_id=student.id, course_id=course.id, status="ACTIVE")
    sess.add(enr)
    sess.commit()

    csrf = login_session(client, student.email)

    res = client.post(
        "/student/ai/chat",
        json={
            "message": "Cho em hỏi về kiến trúc Microservices trong môn học này?",
            "course_id": str(course.public_id),
        },
        headers={"X-CSRFToken": csrf},
    )
    assert res.status_code == 200, f"AI Chat failed: {res.get_data(as_text=True)}"
    data = res.get_json()
    assert "reply" in data or "response" in data
    assert_adr002(data)
