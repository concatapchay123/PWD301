"""Verification test suite for Instructor Academic Governance & Exam Studio fixes."""

import json

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.identity import Role, User
from pwd301.services.course_service import create_course
from pwd301.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
    """Ensure canonical roles exist."""
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
def test_instructor(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create a verified test instructor."""
    u = register_user("test_instructor_fix@example.com", "Password@123", "Giảng viên Kiểm thử")
    return assign_role_to_user(u.id, "INSTRUCTOR")


def test_slo_and_completion_rules_persistence(
    client: FlaskClient, test_instructor: User, app: Flask
) -> None:
    """Test that SLO standards and completion rules persist and serialize correctly."""
    login_web_user(client, test_instructor)

    # Create draft course
    course = create_course(
        test_instructor,
        {
            "course_code": "TEST-SLO-101",
            "title": "Khóa học Kiểm thử SLO",
            "summary": "Mô tả khóa học kiểm thử",
        },
        session=db.session,
    )
    course_id = str(course.public_id)

    # 1. Update Course with custom SLO standards (learning_objectives)
    slo_data = [
        {
            "code": "SLO-01",
            "name": "Hiểu kiến trúc REST",
            "description": "Nắm vững nguyên lý Stateless và HATEOAS",
        },
        {
            "code": "SLO-02",
            "name": "Thiết kế CSDL",
            "description": "Thiết kế lược đồ chuẩn hóa 3NF",
        },
    ]
    res_update = client.post(
        f"/instructor/courses/{course_id}",
        json={
            "learning_objectives": slo_data,
            "target_audience": "Sinh viên năm 3",
            "completion_requirements": {"min_score": 7.5},
        },
    )
    assert res_update.status_code in (200, 201), (
        f"Update course failed: {res_update.get_data(as_text=True)}"
    )
    c_info = res_update.get_json()
    assert c_info.get("learning_objectives") is not None

    # Verify GET /instructor/courses/<id> returns learning_objectives
    res_get = client.get(f"/instructor/courses/{course_id}")
    assert res_get.status_code == 200
    get_data = res_get.get_json()
    retrieved_slos = get_data.get("learning_objectives")
    assert retrieved_slos is not None
    if isinstance(retrieved_slos, str):
        parsed = json.loads(retrieved_slos)
        assert len(parsed) == 2
        assert parsed[0]["code"] == "SLO-01"
    else:
        assert len(retrieved_slos) == 2

    # Publish course so it is viewable across public API and student views
    course.status = "PUBLISHED"
    db.session.commit()

    # Verify GET /api/courses/<id> returns learning_objectives
    res_api = client.get(f"/api/courses/{course_id}")
    assert res_api.status_code == 200
    api_course = res_api.get_json()
    assert api_course.get("learning_objectives") is not None
    assert len(api_course.get("learning_objectives")) == 2
    assert api_course["learning_objectives"][0]["code"] == "SLO-01"

    # Verify student course view returns parsed learning_objectives
    stu = register_user("student_slo_chk@example.com", "Password@123", "Sinh viên SLO")
    assign_role_to_user(stu.id, "STUDENT")
    login_web_user(client, stu)
    res_stu = client.get(f"/student/courses/{course_id}")
    assert res_stu.status_code == 200
    stu_course = res_stu.get_json()["course"]
    assert stu_course.get("learning_objectives") is not None
    assert len(stu_course.get("learning_objectives")) == 2
    assert stu_course["learning_objectives"][0]["code"] == "SLO-01"

    # Re-login instructor for subsequent tests
    login_web_user(client, test_instructor)

    # 2. Update completion rule (minimum_grade_score, allow_certificate, grace_days)
    res_comp = client.post(
        f"/instructor/courses/{course_id}/completion-rules",
        json={
            "required_percentage": 80.0,
            "minimum_grade_score": 6.5,
            "allow_certificate": True,
            "completion_grace_days": 14,
        },
    )
    assert res_comp.status_code == 200, (
        f"Completion rule save failed: {res_comp.get_data(as_text=True)}"
    )
    comp_json = res_comp.get_json()
    assert comp_json.get("minimum_grade_score") == 6.5
    assert comp_json.get("allow_certificate") is True
    assert comp_json.get("completion_grace_days") == 14

    # Verify GET /instructor/courses/<id>/completion-rules retrieves saved values
    res_comp_get = client.get(f"/instructor/courses/{course_id}/completion-rules")
    assert res_comp_get.status_code == 200
    comp_get_data = res_comp_get.get_json()
    assert comp_get_data.get("minimum_grade_score") == 6.5
    assert comp_get_data.get("allow_certificate") is True


def test_lesson_duration_summary_video_persistence(
    client: FlaskClient, test_instructor: User, app: Flask
) -> None:
    """Test that lesson duration, summary, description, and YouTube links are persisted."""
    login_web_user(client, test_instructor)

    course = create_course(
        test_instructor,
        {
            "course_code": "TEST-LES-202",
            "title": "Khóa học Bài giảng",
            "summary": "Mô tả khóa học",
        },
        session=db.session,
    )
    course_id = str(course.public_id)

    # 1. Create a lesson with duration, summary, video
    res_create = client.post(
        f"/instructor/courses/{course_id}/lessons",
        json={
            "title": "Bài 1: Kiến trúc Client-Server",
            "summary": "Tóm tắt về mô hình truyền thông Client-Server và HTTP Protocol.",
            "markdown_content": "# Nội dung bài giảng số 1\nChi tiết kiến trúc...",
            "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "estimated_duration_minutes": 25,
            "status": "DRAFT",
        },
    )
    assert res_create.status_code in (200, 201), (
        f"Create lesson failed: {res_create.get_data(as_text=True)}"
    )
    les_data = res_create.get_json()
    lesson_id = les_data.get("lesson_id") or les_data.get("id")

    # 2. Get lesson details to verify fields
    res_get = client.get(f"/instructor/lessons/{lesson_id}")
    assert res_get.status_code == 200
    lesson_info = res_get.get_json()
    assert (
        lesson_info["summary"] == "Tóm tắt về mô hình truyền thông Client-Server và HTTP Protocol."
    )
    assert lesson_info["estimated_duration_minutes"] == 25
    assert "youtube.com" in (lesson_info.get("video_url") or "")

    # 3. Update lesson duration and YouTube URL
    res_update = client.put(
        f"/instructor/lessons/{lesson_id}",
        json={
            "title": "Bài 1: Kiến trúc Client-Server (Cập nhật)",
            "summary": "Tóm tắt nâng cao.",
            "estimated_duration_minutes": 40,
            "video_url": "https://www.youtube.com/watch?v=kJQP7kiw5Fk",
        },
    )
    assert res_update.status_code in (200, 201), (
        f"Update lesson failed: {res_update.get_data(as_text=True)}"
    )
    updated_info = res_update.get_json()
    assert updated_info["estimated_duration_minutes"] == 40
    assert updated_info["summary"] == "Tóm tắt nâng cao."


def test_assessment_results_endpoint_success(
    client: FlaskClient, test_instructor: User, app: Flask
) -> None:
    """Test that fetching assessment results by ID succeeds without 404."""
    login_web_user(client, test_instructor)

    course = create_course(
        test_instructor,
        {
            "course_code": "TEST-ASM-303",
            "title": "Khóa học Khảo thí",
            "summary": "Khóa học khảo thí",
        },
        session=db.session,
    )

    from datetime import timedelta

    from pwd301.models.types import utc_now
    from pwd301.services.assessment_service import create_assessment

    now = utc_now()
    asm = create_assessment(
        test_instructor,
        course.id,
        {
            "title": "Bài kiểm tra Giữa kỳ",
            "assessment_type": "MIDTERM",
            "open_at": (now + timedelta(days=1)).isoformat(),
            "close_at": (now + timedelta(days=3)).isoformat(),
            "time_limit_minutes": 45,
            "passing_percent": 60.0,
        },
        session=db.session,
    )
    asm_id = str(asm.public_id)

    # Call attempts/results endpoint with assessment_id
    res = client.get(f"/instructor/assessments/{asm_id}/attempts")
    assert res.status_code == 200, (
        f"Expected 200 OK, got {res.status_code}: {res.get_data(as_text=True)}"
    )
    data = res.get_json()
    assert "attempts" in data
    assert "assessment_id" in data
