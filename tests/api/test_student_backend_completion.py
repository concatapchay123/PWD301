"""TDD Test Suite for TASK-052: Student Role Backend Completion & Security Hardening.

Verifies:
1. Student assessments endpoint payload parity (items, assessments, upcoming, recent_results).
2. Student attempt result academic metrics (letter_grade, GPA, percentile, proctoring_verified)
   and score release policy.
3. Student course detail ADR-002 compliance (zero internal PK leakage) and
   Fail-Closed ClamAV filtering.
4. Student my-learning dual envelope (enrollments & courses) and AI RAG contextual enrollment
   authorization (IDOR defense).
5. Student become-instructor workflow, zero PK leakage & 100% UTF-8 integrity.
"""

from __future__ import annotations

import io
import json
import uuid
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
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


def login_client(client: FlaskClient, email: str, password: str = "Password@123") -> str:
    """Helper to authenticate a client via web session and extract CSRF token."""
    res = client.get("/auth/login")
    data = res.get_json() or {}
    csrf_token = data.get("csrf_token", "")

    login_res = client.post(
        "/auth/login",
        json={"email": email, "password": password},
        headers={"X-CSRFToken": csrf_token},
    )
    assert login_res.status_code == 200
    return csrf_token


@pytest.fixture
def student_fixture(app: Flask) -> dict[str, Any]:
    """Setup complete test fixture for student backend verification."""
    sess: Session = db.session
    seed_baseline(sess)

    # 1. Instructor & Student
    instructor = register_user(
        email="instructor_stu@pwd301.local",
        password="Password@123",
        display_name="TS. Doan Giang Vien",
        session=sess,
    )
    assign_role_to_user(instructor.id, "INSTRUCTOR", session=sess)

    student = register_user(
        email="student_stu@pwd301.local",
        password="Password@123",
        display_name="Nguyen Van Sinh Vien",
        session=sess,
    )
    assign_role_to_user(student.id, "STUDENT", session=sess)

    # 2. Enrolled Course
    course = create_course(
        actor=instructor,
        data={
            "course_code": "STU301",
            "title": "Lap trinh Web Chuyen sau",
            "category": "Computer Science",
            "capacity": 50,
        },
        session=sess,
    )
    course.status = "PUBLISHED"
    sess.flush()

    enr = Enrollment(
        student_user_id=student.id,
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

    # 3. Unenrolled Course (for IDOR testing)
    unenrolled_course = create_course(
        actor=instructor,
        data={
            "course_code": "SEC999",
            "title": "Bao mat He thong Nang cao",
            "category": "Security",
            "capacity": 30,
        },
        session=sess,
    )
    unenrolled_course.status = "PUBLISHED"
    sess.flush()

    # 4. Lesson in enrolled course
    lesson = create_lesson(
        actor=instructor,
        course_id=course.id,
        data={
            "title": "Bai 1: Kien truc Web Microservices",
            "summary": "Tong quan kien truc Web Microservices",
            "markdown_content": "# Kien truc Web Microservices",
            "estimated_duration_minutes": 45,
            "status": "PUBLISHED",
        },
        session=sess,
    )

    # 5. Clean File Asset
    clean_stream = io.BytesIO(b"Noi dung tai lieu sach ClamAV")
    clean_asset = store_file_stream(
        actor=instructor,
        course_id=course.id,
        file_stream=clean_stream,
        filename="lecture_clean.pdf",
        content_type="application/pdf",
        asset_type="LECTURE_SLIDE",
        session=sess,
    )
    clean_asset.status = "ACTIVE"
    sess.flush()

    attach_resource_to_lesson(
        actor=instructor,
        lesson_id=lesson.id,
        asset_id=clean_asset.id,
        label="Slide Sach ClamAV",
        is_downloadable=True,
        session=sess,
    )

    # 6. Quarantined / Unscanned File Asset
    dirty_stream = io.BytesIO(b"Noi dung chua quet virus")
    dirty_asset = store_file_stream(
        actor=instructor,
        course_id=course.id,
        file_stream=dirty_stream,
        filename="unscanned_file.zip",
        content_type="application/zip",
        asset_type="ASSIGNMENT_BRIEF",
        session=sess,
    )
    dirty_asset.status = "PENDING"
    if dirty_asset.revisions:
        dirty_asset.revisions[0].status = "QUARANTINED"
    sess.flush()

    attach_resource_to_lesson(
        actor=instructor,
        lesson_id=lesson.id,
        asset_id=dirty_asset.id,
        label="File Chua Quet",
        is_downloadable=True,
        session=sess,
    )

    # 7. Questions
    q1 = create_question(
        actor=instructor,
        course_id=course.id,
        payload={
            "question_type": "SINGLE_CHOICE",
            "difficulty": "UNDERSTAND",
            "content": "Giao thuc HTTP dung cho Web la gi?",
            "explanation": "HTTP la Hypertext Transfer Protocol.",
            "choices": [
                {"content": "Hypertext Transfer Protocol", "is_correct": True, "position": 1},
                {"content": "High Transfer Protocol", "is_correct": False, "position": 2},
            ],
        },
        session=sess,
    )

    # 8. Assessment
    assessment = create_assessment(
        actor=instructor,
        course_id=course.id,
        payload={
            "title": "Khao thi Thuong ky Web",
            "assessment_type": "QUIZ",
            "time_limit_minutes": 30,
            "passing_score": 5.0,
            "score_release_policy": "IMMEDIATE",
        },
        session=sess,
    )
    assign_question(
        actor=instructor,
        assessment_id=assessment.id,
        payload={"question_id": q1.id, "points": 10.0},
        session=sess,
    )
    publish_assessment(actor=instructor, assessment_id=assessment.id, session=sess)
    sess.commit()

    return {
        "instructor": instructor,
        "student": student,
        "course": course,
        "unenrolled_course": unenrolled_course,
        "lesson": lesson,
        "assessment": assessment,
        "question": q1,
        "clean_asset": clean_asset,
        "dirty_asset": dirty_asset,
    }


def test_student_assessments_endpoint_payload_parity(
    client: FlaskClient, student_fixture: dict[str, Any]
) -> None:
    """Verify GET /student/assessments returns items, assessments, upcoming, and recent_results."""
    login_client(client, "student_stu@pwd301.local")
    res = client.get("/student/assessments", headers={"Accept": "application/json"})
    assert res.status_code == 200
    data = res.get_json()

    # Must contain both items and assessments for frontend renderAssessmentsList compatibility
    assert "items" in data, "Must contain 'items' array for StudentView.renderAssessmentsList"
    assert "assessments" in data, "Must contain 'assessments' array"
    assert "upcoming" in data
    assert "recent_results" in data

    items = data["items"]
    assert len(items) >= 1
    target = next((item for item in items if item["title"] == "Khao thi Thuong ky Web"), None)
    assert target is not None
    assert uuid.UUID(target["assessment_id"])  # Must be valid UUID
    assert target["course_code"] == "STU301"
    assert target["time_limit_minutes"] == 30
    assert float(target["max_points"]) == 10.0
    assert target["status"] == "PUBLISHED"


def test_student_attempt_result_academic_metrics_and_release_policy(
    client: FlaskClient, student_fixture: dict[str, Any]
) -> None:
    """Verify attempt result provides server-authoritative metrics and honors release policy."""
    csrf = login_client(client, "student_stu@pwd301.local")
    asm_id = str(student_fixture["assessment"].public_id)

    # 1. Start assessment
    start_res = client.post(
        f"/student/assessments/{asm_id}/start",
        headers={"X-CSRFToken": csrf, "Accept": "application/json"},
    )
    assert start_res.status_code == 201
    start_data = start_res.get_json()
    attempt_id = start_data["attempt_id"]
    lease_token = start_data.get("lease_token", "")

    # 2. Get delivery & answer correctly
    deliv = client.get(f"/student/attempt/{attempt_id}").get_json()
    q1 = deliv["questions"][0]
    correct_choice = next(c for c in q1["choices"] if c["position"] == 1)
    c_key = correct_choice.get("choice_key") or correct_choice.get("choice_id")

    client.post(
        f"/student/attempt/{attempt_id}/answers/{q1['attempt_question_id']}",
        headers={"X-CSRFToken": csrf, "X-Attempt-Lease-Token": lease_token},
        json={"selected_choice_key": c_key, "client_sequence": 1},
    )

    # 3. Submit attempt
    submit_res = client.post(
        f"/student/attempt/{attempt_id}/submit",
        headers={"X-CSRFToken": csrf, "X-Attempt-Lease-Token": lease_token},
        json={},
    )
    assert submit_res.status_code == 200

    # 4. Query result
    result_res = client.get(f"/student/attempt/{attempt_id}/result")
    assert result_res.status_code == 200
    res_data = result_res.get_json()

    # Server-authoritative academic indicators
    assert res_data.get("letter_grade") == "A"
    assert "Xuất sắc" in (res_data.get("grade_descriptor") or "")
    assert float(res_data.get("gpa") or 0.0) == 4.0
    assert res_data.get("is_passed") is True
    assert res_data.get("proctoring_verified") is True
    assert "percentile_text" in res_data


def test_student_course_detail_adr002_and_clamav_fail_closed(
    client: FlaskClient, student_fixture: dict[str, Any]
) -> None:
    """Verify GET /student/courses/<id> leaks NO internal PKs and filters dirty/unscanned files."""
    login_client(client, "student_stu@pwd301.local")
    course_id = str(student_fixture["course"].public_id)

    res = client.get(f"/student/courses/{course_id}", headers={"Accept": "application/json"})
    assert res.status_code == 200
    data = res.get_json()

    # ADR-002 Zero Internal PK Leakage checks
    course_data = data["course"]
    assert isinstance(course_data["id"], str)
    assert uuid.UUID(course_data["id"])
    assert uuid.UUID(course_data["public_id"])

    # Enrollment ID must be UUID string
    if data.get("enrollment"):
        assert isinstance(data["enrollment"]["id"], str)
        assert uuid.UUID(data["enrollment"]["id"])

    # Lessons IDs must be UUID string
    assert len(data["lessons"]) >= 1
    for les in data["lessons"]:
        assert isinstance(les["id"], str)
        assert uuid.UUID(les["id"])
        assert uuid.UUID(les["lesson_id"])

        # Fail-Closed ClamAV: only clean files in lesson resources
        for r in les.get("resources", []):
            fa = r.get("file_asset") or {}
            assert fa.get("virus_scan_status") == "CLEAN", (
                "Unscanned or dirty files must not be exposed to students"
            )

    # Course level resources: only CLEAN files
    for r in data.get("resources", []):
        assert r.get("resource_id")
        assert uuid.UUID(r["resource_id"])
        assert "unscanned" not in r.get("label", "").lower()


def test_student_my_learning_dual_envelope_and_ai_rag_idor_defense(
    client: FlaskClient, student_fixture: dict[str, Any]
) -> None:
    """Verify my-learning returns enrollments & courses, and AI chat enforces enrollment check."""
    csrf = login_client(client, "student_stu@pwd301.local")

    # 1. Test my-learning dual envelope
    res = client.get("/student/my-learning")
    assert res.status_code == 200
    data = res.get_json()
    assert "enrollments" in data
    assert "courses" in data
    courses = data["courses"]
    assert len(courses) >= 1
    first_c = courses[0]
    assert "course_id" in first_c
    assert "course_code" in first_c
    assert "title" in first_c

    # 2. Test AI Chat IDOR defense on unenrolled course
    unenrolled_id = str(student_fixture["unenrolled_course"].public_id)
    chat_res = client.post(
        "/student/ai/chat",
        headers={"X-CSRFToken": csrf, "Accept": "application/json"},
        json={"message": "Tom tat noi dung khoa hoc nay", "course_id": unenrolled_id},
    )
    # Must be forbidden or rejected due to unenrolled course
    assert chat_res.status_code in (403, 400)
    err_body = chat_res.get_json()
    assert (
        "error" in err_body
        or err_body.get("status") in ("refused", "error")
        or "enroll" in str(err_body).lower()
    )


def test_student_cannot_force_lesson_completion_from_progress_payload(
    client: FlaskClient, student_fixture: dict[str, Any]
) -> None:
    """The progress endpoint must derive completion instead of trusting client input."""
    csrf = login_client(client, "student_stu@pwd301.local")
    lesson_id = str(student_fixture["lesson"].public_id)

    response = client.post(
        f"/student/lessons/{lesson_id}/progress",
        headers={"X-CSRFToken": csrf, "Accept": "application/json"},
        json={"seconds_increment": 1, "completed": True},
    )

    assert response.status_code == 200
    assert response.get_json()["is_completed"] is False


def test_student_lesson_hides_unscanned_resources(
    client: FlaskClient, student_fixture: dict[str, Any]
) -> None:
    """Unscanned assets must not appear as accessible learning resources."""
    lesson = student_fixture["lesson"]
    asset = student_fixture["clean_asset"]
    asset.status = "PENDING"
    db.session.commit()
    login_client(client, "student_stu@pwd301.local")

    response = client.get(
        f"/student/courses/{student_fixture['course'].public_id}/lessons/{lesson.public_id}"
    )

    assert response.status_code == 200
    assert response.get_json()["resources"] == []


def test_student_lesson_shows_resources_attached_to_that_lesson(
    client: FlaskClient, student_fixture: dict[str, Any]
) -> None:
    """A clean file attached to a lesson appears in that lesson's detail response."""
    lesson = student_fixture["lesson"]
    login_client(client, "student_stu@pwd301.local")

    response = client.get(
        f"/student/courses/{student_fixture['course'].public_id}/lessons/{lesson.public_id}"
    )

    assert response.status_code == 200
    resources = response.get_json()["resources"]
    assert len(resources) == 1
    assert resources[0]["filename"] == "lecture_clean.pdf"
    assert "/student/courses/" in resources[0]["download_url"]


def test_student_course_detail_hides_unpublished_lessons(
    client: FlaskClient, student_fixture: dict[str, Any]
) -> None:
    """Student course detail must never serialize instructor drafts."""
    draft = create_lesson(
        actor=student_fixture["instructor"],
        course_id=student_fixture["course"].id,
        data={"title": "Private draft", "markdown_content": "draft", "status": "DRAFT"},
        session=db.session,
    )
    db.session.commit()
    login_client(client, "student_stu@pwd301.local")

    response = client.get(f"/student/courses/{student_fixture['course'].public_id}")

    assert response.status_code == 200
    lesson_ids = {item["lesson_id"] for item in response.get_json()["lessons"]}
    assert str(student_fixture["lesson"].public_id) in lesson_ids
    assert str(draft.public_id) not in lesson_ids


def test_student_lesson_with_mini_quiz_stays_incomplete_until_every_answer_is_submitted(
    client: FlaskClient, student_fixture: dict[str, Any]
) -> None:
    """Completing video progress alone must not complete a lesson that has a mini-quiz."""
    lesson = student_fixture["lesson"]
    quiz = [
        {
            "type": "MULTIPLE_CHOICE",
            "question": "Which protocol serves a web page?",
            "options": ["HTTP", "FTP"],
            "correct_answers": [0],
        }
    ]
    lesson.markdown_content = (
        "# Lesson\n\n<!-- video_url: https://videos.example/lesson.mp4 -->\n\n<!-- mini_quiz: "
        + json.dumps(quiz)
        + " -->"
    )
    db.session.commit()
    csrf = login_client(client, "student_stu@pwd301.local")

    early_quiz = client.post(
        f"/student/lessons/{lesson.public_id}/quiz-completion",
        headers={"X-CSRFToken": csrf, "Accept": "application/json"},
        json={"answers": [[0]]},
    )
    assert early_quiz.status_code in (400, 409)

    partial_progress = client.post(
        f"/student/lessons/{lesson.public_id}/progress",
        headers={"X-CSRFToken": csrf, "Accept": "application/json"},
        json={"seconds_increment": 60, "view_fraction": 0.8, "completed": True},
    )

    assert partial_progress.status_code == 200
    assert partial_progress.get_json()["is_completed"] is False

    partial_video_quiz = client.post(
        f"/student/lessons/{lesson.public_id}/quiz-completion",
        headers={"X-CSRFToken": csrf, "Accept": "application/json"},
        json={"answers": [[0]]},
    )
    assert partial_video_quiz.status_code in (400, 409)

    full_progress = client.post(
        f"/student/lessons/{lesson.public_id}/progress",
        headers={"X-CSRFToken": csrf, "Accept": "application/json"},
        json={"seconds_increment": 60, "view_fraction": 1.0, "completed": True},
    )
    assert full_progress.status_code == 200

    incomplete_quiz = client.post(
        f"/student/lessons/{lesson.public_id}/quiz-completion",
        headers={"X-CSRFToken": csrf, "Accept": "application/json"},
        json={"answers": []},
    )
    assert incomplete_quiz.status_code == 400

    complete_quiz = client.post(
        f"/student/lessons/{lesson.public_id}/quiz-completion",
        headers={"X-CSRFToken": csrf, "Accept": "application/json"},
        json={"answers": [[0]]},
    )
    assert complete_quiz.status_code == 200
    assert complete_quiz.get_json()["is_completed"] is True


def test_video_only_lesson_requires_full_view_fraction_before_completion(
    client: FlaskClient, student_fixture: dict[str, Any]
) -> None:
    lesson = student_fixture["lesson"]
    lesson.markdown_content = "# Lesson\n\n<!-- video_url: https://videos.example/lesson.mp4 -->"
    db.session.commit()
    csrf = login_client(client, "student_stu@pwd301.local")

    partial = client.post(
        f"/student/lessons/{lesson.public_id}/progress",
        headers={"X-CSRFToken": csrf, "Accept": "application/json"},
        json={"seconds_increment": 60, "view_fraction": 0.8},
    )
    assert partial.status_code == 200
    assert partial.get_json()["is_completed"] is False

    full = client.post(
        f"/student/lessons/{lesson.public_id}/progress",
        headers={"X-CSRFToken": csrf, "Accept": "application/json"},
        json={"seconds_increment": 60, "view_fraction": 1.0},
    )
    assert full.status_code == 200
    assert full.get_json()["is_completed"] is True


def test_student_cannot_complete_a_malformed_mini_quiz(student_fixture, client):
    lesson = student_fixture["lesson"]
    lesson.markdown_content = '# Lesson\n\n<!-- mini_quiz: [{"type":"UNSUPPORTED"},null] -->'
    db.session.flush()

    token = login_client(client, "student_stu@pwd301.local")
    response = client.post(
        f"/student/lessons/{lesson.public_id}/quiz-completion",
        json={"answers": ["anything", "anything"]},
        headers={"X-CSRFToken": token},
    )

    assert response.status_code == 400


def test_student_become_instructor_and_utf8_integrity(
    client: FlaskClient, student_fixture: dict[str, Any]
) -> None:
    """Verify instructor nomination endpoints do not leak PKs and return clean UTF-8 JSON."""
    csrf = login_client(client, "student_stu@pwd301.local")

    # 1. GET become-instructor
    res_get = client.get("/student/become-instructor")
    assert res_get.status_code == 200
    data_get = res_get.get_json()
    assert data_get["is_already_instructor"] is False

    # 2. POST submit become-instructor
    res_post = client.post(
        "/student/become-instructor",
        headers={"X-CSRFToken": csrf, "Accept": "application/json"},
        json={
            "institution_name": "Đại học Bách Khoa TP.HCM",
            "specialization": "Kỹ thuật Phần mềm & An toàn Thông tin",
            "experience_years": 5,
            "certificate_url": "https://cloud.pwd301.edu.vn/cv/sample.pdf",
            "statement": "Tôi mong muốn giảng dạy các học phần Web Security và Phân tán.",
        },
    )
    assert res_post.status_code == 201
    post_data = res_post.get_json()
    assert "application_id" in post_data
    # Must be UUID string, NOT integer BigInt
    assert isinstance(post_data["application_id"], str)
    assert uuid.UUID(post_data["application_id"])
    assert "thành công" in post_data.get("message", "").lower()

    # 3. POST cancel application
    res_cancel = client.post(
        "/student/become-instructor/cancel",
        headers={"X-CSRFToken": csrf, "Accept": "application/json"},
    )
    assert res_cancel.status_code == 200
    cancel_data = res_cancel.get_json()
    assert "hủy" in cancel_data.get("message", "").lower()
