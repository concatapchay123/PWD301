"""Tests for Instructor Exam Parse File API and File Download routes."""

from __future__ import annotations

import io
import uuid

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course
from pwd301.models.identity import Role, User
from pwd301.services.course_service import create_course
from pwd301.services.user_service import assign_role_to_user, register_user
from tests.api.test_docx_image_extraction import create_sample_docx_with_images
from tests.conftest import login_web_user


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
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
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    email = f"exam_inst_{uuid.uuid4().hex[:6]}@example.com"
    u = register_user(email, "Password@123", "Exam Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def instructor_client(client: FlaskClient, instructor_user: User) -> FlaskClient:
    login_web_user(client, instructor_user)
    with client.session_transaction() as sess:
        sess["active_role"] = "INSTRUCTOR"
    return client


@pytest.fixture
def sample_course(app: Flask, instructor_user: User) -> Course:
    sess: Session = db.session
    course = create_course(
        actor=instructor_user,
        data={
            "course_code": f"EXAM{uuid.uuid4().hex[:4].upper()}",
            "title": "Exam Testing Course",
            "credits": 3,
        },
        session=sess,
    )
    sess.commit()
    return course


def test_parse_docx_with_images_extracts_and_saves_file_assets(
    instructor_client: FlaskClient,
    sample_course: Course,
):
    """Test that POST /instructor/exams/parse-file converts docx images into FileAssets."""
    docx_bytes = create_sample_docx_with_images()
    data = {
        "file": (io.BytesIO(docx_bytes), "sample_exam.docx"),
        "course_id": str(sample_course.public_id),
    }

    res = instructor_client.post(
        "/instructor/exams/parse-file",
        data=data,
        content_type="multipart/form-data",
    )
    assert res.status_code == 200
    res_data = res.get_json()
    assert res_data["success"] is True
    assert "raw_text" in res_data
    assert "[[PWD301:IMAGE:" in res_data["raw_text"]
    assert "extracted_images" in res_data
    assert len(res_data["extracted_images"]) >= 1

    first_image = res_data["extracted_images"][0]
    asset_id = first_image["asset_id"]
    assert asset_id is not None

    # Test download route without course_id: GET /instructor/files/<asset_id>/download
    dl_res = instructor_client.get(f"/instructor/files/{asset_id}/download?disposition=inline")
    assert dl_res.status_code == 200
    assert dl_res.content_type in ("image/png", "image/jpeg")
    assert len(dl_res.data) > 0


def test_upload_course_file_route_unified(
    instructor_client: FlaskClient,
    sample_course: Course,
    instructor_user: User,
):
    """Verify that POST /instructor/courses/<course_id>/files works reliably with file upload."""
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    data = {
        "file": (io.BytesIO(png_bytes), "sample_img.png"),
        "title": "Sample Image",
        "asset_type": "RESOURCE",
    }
    res = instructor_client.post(
        f"/instructor/courses/{sample_course.public_id}/files",
        data=data,
        content_type="multipart/form-data",
    )
    assert res.status_code == 201
    res_data = res.get_json()
    assert "asset_id" in res_data
