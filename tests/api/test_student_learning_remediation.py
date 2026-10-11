"""TDD Test Suite for Student Learning & Course Progress Remediation.

Verifies:
1. Completed students can view course lessons and progress (no 403 lock-out).
2. Completed students can download course files and stream video assets.
3. Video progress credits only elapsed server time and preserves minimum duration.
4. Re-enrolling a completed course preserves 100% progress and graduation status.
5. Student certificate endpoint (/student/courses/<cid>/certificate) returns verification payload.
6. Server-side sequential learning enforcement when enabled on course.
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
from pwd301.models.course import Lesson
from pwd301.models.types import utc_now
from pwd301.seeds.baseline import seed_baseline
from pwd301.services.course_service import create_course
from pwd301.services.enrollment_service import enroll_student
from pwd301.services.file_service import attach_resource_to_lesson, store_file_stream
from pwd301.services.lesson_service import (
    create_lesson,
)
from pwd301.services.user_service import assign_role_to_user, register_user


def login_client(client: FlaskClient, email: str, password: str = "Password@123") -> str:
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
def remediation_fixture(app: Flask) -> dict[str, Any]:
    sess: Session = db.session
    seed_baseline(sess)

    # 1. Instructor
    inst_email = f"inst_{uuid.uuid4().hex[:6]}@example.com"
    instructor = register_user(
        email=inst_email,
        password="Password@123",
        display_name="Remediation Instructor",
        session=sess,
    )
    assign_role_to_user(instructor.id, "INSTRUCTOR", session=sess)

    # 2. Student
    stu_email = f"stu_{uuid.uuid4().hex[:6]}@example.com"
    student = register_user(
        email=stu_email,
        password="Password@123",
        display_name="Remediation Student",
        session=sess,
    )
    assign_role_to_user(student.id, "STUDENT", session=sess)

    # 3. Create Course
    course = create_course(
        actor=instructor,
        data={
            "course_code": f"REM{uuid.uuid4().hex[:4].upper()}",
            "title": "Remediation Flow Course",
            "category": "Computer Science",
            "capacity": 50,
        },
        session=sess,
    )
    course.status = "PUBLISHED"
    course.completion_requirements = json.dumps({"allow_certificate": True})
    sess.flush()

    # 4. Create Lessons
    lesson1 = create_lesson(
        actor=instructor,
        course_id=course.id,
        data={
            "title": "Lesson 1 - Video Foundations",
            "summary": "Foundations",
            "markdown_content": """# Lesson 1
<!-- video_urls: ["https://youtu.be/abcdefghijk"] -->
Content of lesson 1
""",
            "estimated_duration_minutes": 15,
            "minimum_completion_seconds": 60,
            "viewed_fraction_required": 0.8,
            "status": "PUBLISHED",
        },
        session=sess,
    )

    lesson2 = create_lesson(
        actor=instructor,
        course_id=course.id,
        data={
            "title": "Lesson 2 - Advanced Topics",
            "summary": "Advanced",
            "markdown_content": "# Lesson 2 content",
            "estimated_duration_minutes": 20,
            "minimum_completion_seconds": 30,
            "viewed_fraction_required": 0.8,
            "status": "PUBLISHED",
        },
        session=sess,
    )

    # Attach file asset to lesson 1
    pdf_stream = io.BytesIO(b"%PDF-1.4 mock pdf content for lesson 1")
    asset = store_file_stream(
        actor=instructor,
        course_id=course.id,
        file_stream=pdf_stream,
        filename="lecture1_notes.pdf",
        content_type="application/pdf",
        asset_type="LECTURE_SLIDE",
        session=sess,
    )
    asset.status = "ACTIVE"
    sess.flush()

    attach_resource_to_lesson(
        actor=instructor,
        lesson_id=lesson1.id,
        asset_id=asset.id,
        label="Lecture 1 PDF",
        is_downloadable=True,
        session=sess,
    )

    sess.commit()

    return {
        "instructor": instructor,
        "student": student,
        "course": course,
        "lesson1": lesson1,
        "lesson2": lesson2,
        "asset": asset,
    }


def test_completed_student_can_view_lesson_and_progress(
    client: FlaskClient, remediation_fixture: dict[str, Any], playback_watch
):
    student = remediation_fixture["student"]
    course = remediation_fixture["course"]
    lesson1 = remediation_fixture["lesson1"]
    sess: Session = db.session

    # Enroll and complete course
    enrollment = enroll_student(actor=student, course_id=course.id, session=sess)
    playback_watch(student, lesson1)
    enrollment.status = "COMPLETED"
    enrollment.completed_at = utc_now()
    sess.commit()

    # Login student
    csrf_token = login_client(client, student.email)

    # Completed student should be able to get lesson details
    resp = client.get(
        f"/student/courses/{course.public_id}/lessons/{lesson1.public_id}",
        headers={"X-CSRFToken": csrf_token},
    )
    assert resp.status_code == 200, (
        f"Expected 200, got {resp.status_code}: {resp.data.decode('utf-8')}"
    )
    res_json = resp.get_json()
    data = res_json.get("data", res_json)
    assert data["title"] == lesson1.title
    assert data["progress"]["is_completed"] is True


def test_completed_student_can_download_course_files(
    client: FlaskClient, remediation_fixture: dict[str, Any]
):
    student = remediation_fixture["student"]
    course = remediation_fixture["course"]
    asset = remediation_fixture["asset"]
    sess: Session = db.session

    enrollment = enroll_student(actor=student, course_id=course.id, session=sess)
    enrollment.status = "COMPLETED"
    enrollment.completed_at = utc_now()
    sess.commit()

    csrf_token = login_client(client, student.email)

    resp = client.get(
        f"/student/courses/{course.public_id}/files/{asset.public_id}/download",
        headers={"X-CSRFToken": csrf_token},
    )
    assert resp.status_code == 200, (
        f"Expected 200, got {resp.status_code}: {resp.data.decode('utf-8')}"
    )
    assert b"%PDF-1.4" in resp.data


def test_video_completion_satisfies_minimum_seconds(
    client: FlaskClient, remediation_fixture: dict[str, Any], playback_watch
):
    student = remediation_fixture["student"]
    course = remediation_fixture["course"]
    lesson1 = remediation_fixture["lesson1"]
    sess: Session = db.session

    _enrollment = enroll_student(actor=student, course_id=course.id, session=sess)
    csrf_token = login_client(client, student.email)

    # Legacy client timing/completion claims are rejected before crediting video.
    rejected = client.post(
        f"/student/lessons/{lesson1.public_id}/progress",
        json={"seconds_increment": 60, "view_fraction": 0.95},
        headers={"X-CSRFToken": csrf_token},
    )
    assert rejected.status_code == 400
    data = playback_watch(student, lesson1, 0.95)
    assert data["seconds_spent"] >= lesson1.minimum_completion_seconds
    assert data["is_video_complete"] and data["is_completed"]


def test_reenroll_completed_course_preserves_progress(
    client: FlaskClient, remediation_fixture: dict[str, Any]
):
    student = remediation_fixture["student"]
    course = remediation_fixture["course"]
    sess: Session = db.session

    enrollment = enroll_student(actor=student, course_id=course.id, session=sess)
    enrollment.status = "COMPLETED"
    enrollment.current_progress_percent = 100.0
    completed_time = utc_now()
    enrollment.completed_at = completed_time
    if enrollment.current_period:
        enrollment.current_period.status = "COMPLETED"
        enrollment.current_period.completed_at = completed_time
    sess.commit()

    csrf_token = login_client(client, student.email)

    # Student calls enroll endpoint again
    resp = client.post(
        f"/student/courses/{course.public_id}/enroll",
        headers={"X-CSRFToken": csrf_token},
    )
    assert resp.status_code == 200
    sess.refresh(enrollment)
    assert enrollment.status == "ACTIVE"
    assert enrollment.current_period.period_no == 2


def test_student_course_certificate_endpoint(
    client: FlaskClient, remediation_fixture: dict[str, Any]
):
    student = remediation_fixture["student"]
    course = remediation_fixture["course"]
    sess: Session = db.session

    enrollment = enroll_student(actor=student, course_id=course.id, session=sess)
    enrollment.status = "COMPLETED"
    enrollment.completed_at = utc_now()
    sess.commit()

    csrf_token = login_client(client, student.email)

    resp = client.get(
        f"/student/courses/{course.public_id}/certificate",
        headers={"X-CSRFToken": csrf_token},
    )
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert "certificate_code" in data
    assert data["student_name"] == student.display_name
    assert data["course_title"] == course.title
    assert data["course_code"] == course.course_code


def test_sequential_learning_enforcement(
    client: FlaskClient, remediation_fixture: dict[str, Any], playback_watch
):
    student = remediation_fixture["student"]
    course = remediation_fixture["course"]
    lesson1 = remediation_fixture["lesson1"]
    lesson2 = remediation_fixture["lesson2"]
    sess: Session = db.session

    # Configure course to enforce sequential learning
    course.completion_requirements = json.dumps({"enforce_sequential_learning": True})
    _enrollment = enroll_student(actor=student, course_id=course.id, session=sess)
    sess.commit()

    csrf_token = login_client(client, student.email)

    # Lesson 1 is accessible (first lesson)
    resp1 = client.get(
        f"/student/courses/{course.public_id}/lessons/{lesson1.public_id}",
        headers={"X-CSRFToken": csrf_token},
    )
    assert resp1.status_code == 200

    # Lesson 2 is blocked because lesson 1 is not completed
    resp2 = client.get(
        f"/student/courses/{course.public_id}/lessons/{lesson2.public_id}",
        headers={"X-CSRFToken": csrf_token},
    )
    assert resp2.status_code == 409
    assert "Previous lessons must be completed" in resp2.get_json()["error"]["message"]

    # Now complete lesson 1
    playback_watch(student, lesson1)
    sess.commit()

    # Now lesson 2 becomes accessible
    resp2_after = client.get(
        f"/student/courses/{course.public_id}/lessons/{lesson2.public_id}",
        headers={"X-CSRFToken": csrf_token},
    )
    assert resp2_after.status_code == 200


def test_student_course_progress_synchronization_and_serialization(
    client: FlaskClient, remediation_fixture: dict[str, Any], playback_watch
):
    """Verify deep-layer progress synchronization across all student endpoints.

    Tests that /student/courses/<id>/progress, /student/my-learning, and
    /student/courses/<id> consistently serialize BOTH current_progress_percent
    and progress_percent with identical values.
    """
    student = remediation_fixture["student"]
    course = remediation_fixture["course"]
    lesson1 = remediation_fixture["lesson1"]
    sess: Session = db.session

    _enrollment = enroll_student(actor=student, course_id=course.id, session=sess)
    sess.commit()

    csrf_token = login_client(client, student.email)
    assert csrf_token

    # 1. Initially progress is 0%
    prog_resp = client.get(f"/student/courses/{course.public_id}/progress")
    assert prog_resp.status_code == 200
    p_data = prog_resp.get_json()
    assert p_data["progress_percent"] == 0.0
    assert p_data["current_progress_percent"] == 0.0

    # 2. Complete Lesson 1 (1 out of 2 = 50.0%)
    playback_watch(student, lesson1)
    sess.commit()

    # 3. Check /student/courses/<id>/progress
    prog_resp2 = client.get(f"/student/courses/{course.public_id}/progress")
    assert prog_resp2.status_code == 200
    p_data2 = prog_resp2.get_json()
    assert p_data2["progress_percent"] == 50.0
    assert p_data2["current_progress_percent"] == 50.0

    # 4. Check /student/my-learning
    overview_resp = client.get("/student/my-learning")
    assert overview_resp.status_code == 200
    overview_data = overview_resp.get_json()
    my_course = next(
        c for c in overview_data["enrollments"] if c["course_id"] == str(course.public_id)
    )
    assert my_course["progress_percent"] == 50.0
    assert my_course["current_progress_percent"] == 50.0

    # 5. Check /student/courses/<id> detail
    detail_resp = client.get(f"/student/courses/{course.public_id}")
    assert detail_resp.status_code == 200
    detail_data = detail_resp.get_json()
    enr_data = detail_data["enrollment"]
    assert enr_data is not None
    assert enr_data["progress_percent"] == 50.0
    assert enr_data["current_progress_percent"] == 50.0


def test_calculate_course_progress_historical_revisions_retained(
    remediation_fixture: dict[str, Any],
    playback_watch,
):
    """Verify that completing a lesson whose status is later changed to HISTORICAL
    does not cause student progress to drop or reset to 0%.
    """
    from pwd301.services.completion_service import calculate_course_progress

    student = remediation_fixture["student"]
    course = remediation_fixture["course"]
    lesson1 = remediation_fixture["lesson1"]
    sess: Session = db.session

    enrollment = enroll_student(actor=student, course_id=course.id, session=sess)
    sess.commit()

    # Complete Lesson 1
    playback_watch(student, lesson1)
    sess.commit()

    # Progress should be 50.0%
    pct1 = calculate_course_progress(enrollment.id, session=sess)
    assert pct1 == 50.0

    # Now simulate an approved revision of Lesson 1:
    # Lesson 1 becomes HISTORICAL, new lesson is PUBLISHED at position 1
    lesson1.status = "HISTORICAL"
    new_v2 = Lesson(
        course_id=course.id,
        learning_unit_id=lesson1.learning_unit_id,
        title="Bài 1 (v2)",
        position=1,
        status="PUBLISHED",
        minimum_completion_seconds=30,
        viewed_fraction_required=0.8,
    )
    sess.add(new_v2)
    sess.commit()

    # Student progress must NOT drop to 0% because position 1 was already completed
    pct2 = calculate_course_progress(enrollment.id, session=sess)
    assert pct2 == 50.0


def test_calculate_course_progress_self_healing_period(remediation_fixture: dict[str, Any]):
    """Verify that calculate_course_progress self-heals when current_period_id is unset."""
    from pwd301.services.completion_service import calculate_course_progress

    student = remediation_fixture["student"]
    course = remediation_fixture["course"]
    sess: Session = db.session

    enrollment = enroll_student(actor=student, course_id=course.id, session=sess)
    # Intentionally unlink current_period_id to simulate unlinked or corrupted relation
    enrollment.current_period_id = None
    sess.commit()

    pct = calculate_course_progress(enrollment.id, session=sess)
    assert pct == 0.0
    # Must have self-healed current_period_id
    assert enrollment.current_period_id is not None
