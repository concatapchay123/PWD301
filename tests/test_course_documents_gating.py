"""Tests for unenrolled course document protection and gating.

Invariant:
Unenrolled students exploring a course (Catalog -> Course Detail -> Tài liệu)
must NOT receive course file resources in the API payload, and cannot download files (403 Forbidden).
Upon enrolling, the active student gains access to download clean published resources.
"""

from __future__ import annotations

import io
import uuid
from flask import Flask
from flask.testing import FlaskClient
import pytest

from pwd301.extensions import db
from pwd301.models.course import Course, Enrollment, CourseChangeRequest
from pwd301.models.identity import User
from pwd301.services.user_service import register_user, assign_role_to_user
from pwd301.services.course_service import create_course
from pwd301.services.enrollment_service import enroll_student
from tests.conftest import login_web_user


@pytest.fixture
def student_actor(app: Flask) -> User:
    user = register_user(
        email=f"student_{uuid.uuid4().hex[:6]}@example.com",
        password="StudentPassword123!",
        display_name="Nguyen Van A",
    )
    assign_role_to_user(user.id, "STUDENT")
    db.session.commit()
    return user


@pytest.fixture
def instructor_actor(app: Flask) -> User:
    user = register_user(
        email=f"instructor_{uuid.uuid4().hex[:6]}@example.com",
        password="InstructorPassword123!",
        display_name="Thay Giao B",
    )
    assign_role_to_user(user.id, "INSTRUCTOR")
    db.session.commit()
    return user


@pytest.fixture
def published_course_with_file(app: Flask, instructor_actor: User, client: FlaskClient) -> tuple[Course, str]:
    c = create_course(
        instructor_actor,
        {
            "course_code": f"DOC-{uuid.uuid4().hex[:4].upper()}",
            "title": "Document Protection Course",
            "category": "Computer Science",
            "difficulty": "BEGINNER",
        },
    )
    from pwd301.services.lesson_service import create_lesson
    from pwd301.services.file_service import attach_resource_to_lesson
    from pwd301.models.file_import import FileAsset
    les = create_lesson(
        instructor_actor,
        c.id,
        {"title": "Lesson 1", "markdown_content": "# Lesson 1 Content"},
    )

    login_web_user(client, instructor_actor)

    pdf_bytes = b"%PDF-1.4 Gated Document Content"
    up_resp = client.post(
        f"/instructor/courses/{c.public_id}/files",
        data={"file": (io.BytesIO(pdf_bytes), "tailieu.pdf")},
        content_type="multipart/form-data",
        headers={"Accept": "application/json"},
    )
    assert up_resp.status_code in (200, 201)
    asset_id = up_resp.get_json()["asset_id"]

    fa = db.session.query(FileAsset).filter_by(public_id=uuid.UUID(asset_id)).first()
    if fa:
        attach_resource_to_lesson(instructor_actor, les.id, fa.id, label="Tài liệu bài 1", session=db.session)

    c.status = "PUBLISHED"
    les.status = "PUBLISHED"
    db.session.commit()

    return c, asset_id


def test_unenrolled_student_cannot_see_or_download_documents(
    client: FlaskClient,
    student_actor: User,
    published_course_with_file: tuple[Course, str],
) -> None:
    course, asset_id = published_course_with_file

    login_web_user(client, student_actor)

    detail_resp = client.get(f"/student/courses/{course.public_id}", headers={"Accept": "application/json"})
    assert detail_resp.status_code == 200
    data = detail_resp.get_json()

    assert data.get("enrollment") is None
    assert data.get("resources") == []

    dl_resp = client.get(f"/student/courses/{course.public_id}/files/{asset_id}/download")
    assert dl_resp.status_code == 403


def test_enrolled_student_can_see_and_download_documents(
    client: FlaskClient,
    student_actor: User,
    published_course_with_file: tuple[Course, str],
) -> None:
    course, asset_id = published_course_with_file

    enroll_student(student_actor, course.id, session=db.session)
    db.session.commit()

    login_web_user(client, student_actor)

    detail_resp = client.get(f"/student/courses/{course.public_id}", headers={"Accept": "application/json"})
    assert detail_resp.status_code == 200
    data = detail_resp.get_json()

    assert data.get("enrollment") is not None
    # Invariant: Root general course resources list is purged empty
    assert data.get("resources") == []
    # Lesson resources contain the actual learning attachment
    lesson_resources = [r for les in data.get("lessons", []) for r in les.get("resources", [])]
    assert len(lesson_resources) >= 1
    assert any(r.get("asset_id") == asset_id for r in lesson_resources)

    dl_resp = client.get(f"/student/courses/{course.public_id}/files/{asset_id}/download")
    assert dl_resp.status_code == 200
    assert dl_resp.data == b"%PDF-1.4 Gated Document Content"
