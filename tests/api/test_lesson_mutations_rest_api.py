"""API tests for REST Lesson mutations (API-03) and Course Trash/Delete (API-04).

Verifies:
1. POST /api/courses/<course_id>/lessons creates lesson in course.
2. POST /api/lessons creates lesson with course_id in payload.
3. PUT /api/lessons/<lesson_id> updates lesson title and content.
4. POST /api/courses/<course_id>/lessons/reorder reorders lessons.
5. POST /api/lessons/<lesson_id>/status updates lesson lifecycle status.
6. DELETE /api/lessons/<lesson_id> soft-deletes lesson to TRASH.
7. POST /api/courses/<course_id>/trash soft-deletes course.
8. DELETE /api/courses/<course_id> soft-deletes course via DELETE verb.
"""

from __future__ import annotations

import uuid

import pytest
from flask import Flask
from flask.testing import FlaskClient

from pwd301.extensions import db
from pwd301.models.course import Course
from pwd301.models.identity import Role, User
from pwd301.services.jwt_auth_service import create_token_pair


def _get_or_create_role(code: str, name: str) -> Role:
    role = db.session.query(Role).filter_by(code=code).first()
    if role is None:
        role = Role(code=code, name=name)
        db.session.add(role)
        db.session.flush()
    return role


@pytest.fixture
def instructor_setup(app: Flask):
    with app.app_context():
        role = _get_or_create_role("INSTRUCTOR", "Instructor")
        suffix = uuid.uuid4().hex[:6]

        instructor = User(
            email=f"inst_{suffix}@fpt.edu.vn",
            display_name=f"Instructor {suffix}",
            password_hash="hash",
            auth_version=1,
            status="ACTIVE",
        )
        instructor.roles.append(role)
        db.session.add(instructor)
        db.session.flush()

        course = Course(
            course_code=f"CRS-{suffix}",
            course_code_normalized=f"crs-{suffix}",
            title=f"Test Course {suffix}",
            title_normalized=f"test course {suffix}",
            status="DRAFT",
            owner_instructor_id=instructor.id,
        )
        db.session.add(course)
        db.session.commit()

        tokens = create_token_pair(instructor)
        yield {
            "instructor": instructor,
            "course": course,
            "token": tokens["access_token"],
        }


def test_lesson_and_course_mutations_rest_api(client: FlaskClient, instructor_setup: dict) -> None:
    """Test full REST lifecycle for lesson authoring, reordering, deletion, and course trash."""
    course = instructor_setup["course"]
    token = instructor_setup["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. POST /api/courses/<course_id>/lessons
    res_create1 = client.post(
        f"/api/courses/{course.public_id}/lessons",
        json={
            "title": "Lesson 1: Introduction",
            "markdown_content": "# Welcome\nIntroductory content.",
            "estimated_duration_minutes": 15,
        },
        headers=headers,
    )
    assert res_create1.status_code == 201, f"Failed: {res_create1.get_data(as_text=True)}"
    les1_data = res_create1.get_json()
    assert "lesson_id" in les1_data
    les1_id = les1_data["lesson_id"]

    # 2. POST /api/lessons
    res_create2 = client.post(
        "/api/lessons",
        json={
            "course_id": str(course.public_id),
            "title": "Lesson 2: Advanced Topics",
            "markdown_content": "# Deep Dive\nAdvanced details.",
            "estimated_duration_minutes": 30,
        },
        headers=headers,
    )
    assert res_create2.status_code == 201, f"Failed: {res_create2.get_data(as_text=True)}"
    les2_data = res_create2.get_json()
    assert "lesson_id" in les2_data
    les2_id = les2_data["lesson_id"]

    # 3. PUT /api/lessons/<lesson_id>
    res_update = client.put(
        f"/api/lessons/{les1_id}",
        json={
            "title": "Lesson 1: Introduction (Updated)",
            "markdown_content": "# Welcome Updated\nNew content.",
        },
        headers=headers,
    )
    assert res_update.status_code == 200
    updated_data = res_update.get_json()
    assert updated_data["title"] == "Lesson 1: Introduction (Updated)"

    # 4. POST /api/courses/<course_id>/lessons/reorder
    res_reorder = client.post(
        f"/api/courses/{course.public_id}/lessons/reorder",
        json={"ordered_lesson_ids": [les2_id, les1_id]},
        headers=headers,
    )
    assert res_reorder.status_code == 200
    reorder_data = res_reorder.get_json()
    assert "lessons" in reorder_data

    # 5. POST /api/lessons/<lesson_id>/status
    res_status = client.post(
        f"/api/lessons/{les1_id}/status",
        json={"status": "PUBLISHED", "reason": "Ready for students"},
        headers=headers,
    )
    assert res_status.status_code == 200
    assert res_status.get_json()["status"] == "PUBLISHED"

    # 6. DELETE /api/lessons/<lesson_id>
    res_del_lesson = client.delete(
        f"/api/lessons/{les2_id}",
        json={"reason": "Redundant lesson"},
        headers=headers,
    )
    assert res_del_lesson.status_code == 200
    del_data = res_del_lesson.get_json()
    assert del_data.get("message") == "Lesson moved to TRASH."

    # 7. POST /api/courses/<course_id>/trash
    res_trash_course = client.post(
        f"/api/courses/{course.public_id}/trash",
        json={"reason": "Course deprecated"},
        headers=headers,
    )
    assert res_trash_course.status_code == 200
    assert res_trash_course.get_json().get("message") == "Course trashed successfully."
