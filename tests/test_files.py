"""Integration test suite for file management, storage, and security access.

Ensures test runner compatibility when invoking `pytest tests/test_files.py`.
"""

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
from pwd301.services.jwt_auth_service import create_token_pair
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
def file_instructor(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test instructor user."""
    u = register_user("test_files_inst@example.com", "Password@123", "Files Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def file_course(app: Flask, file_instructor: User) -> Course:
    """Create test published course."""
    c = create_course(
        file_instructor,
        {
            "course_code": f"FL-{uuid.uuid4().hex[:4].upper()}",
            "title": "File Management Course",
            "category": "Computer Science",
            "difficulty": "BEGINNER",
        },
    )
    c.status = "PUBLISHED"
    db.session.commit()
    return c


class TestFileManagementOperations:
    """Core file lifecycle and access tests."""

    def test_file_upload_and_metadata(
        self, client: FlaskClient, file_instructor: User, file_course: Course
    ) -> None:
        """Uploading file creates active asset with correct metadata and no PK leaks."""
        tokens = create_token_pair(file_instructor)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        file_data = (io.BytesIO(b"%PDF-1.4 Sample course document"), "course_plan.pdf")
        resp = client.post(
            f"/api/courses/{file_course.public_id}/files",
            data={"file": file_data, "title": "Course Plan"},
            content_type="multipart/form-data",
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["title"] == "Course Plan"
        assert data["original_filename"] == "course_plan.pdf"
        assert data["status"] == "ACTIVE"
        assert "asset_id" in data
        assert "id" not in data

        # GET metadata
        meta_resp = client.get(f"/api/files/{data['asset_id']}", headers=headers)
        assert meta_resp.status_code == 200
        meta_data = meta_resp.get_json()
        assert meta_data["asset_id"] == data["asset_id"]

    def test_instructor_web_session_download(
        self, client: FlaskClient, file_instructor: User, file_course: Course
    ) -> None:
        """Instructor can download file using web session authentication."""
        login_web_user(client, file_instructor)

        doc_content = b"%PDF-1.4 Web session test document"
        up_resp = client.post(
            f"/instructor/courses/{file_course.public_id}/files",
            data={"file": (io.BytesIO(doc_content), "handout.pdf"), "title": "Handout"},
            content_type="multipart/form-data",
            headers={"Accept": "application/json"},
        )
        assert up_resp.status_code == 201
        asset_id = up_resp.get_json()["asset_id"]

        # Download via instructor web route
        dl_resp = client.get(
            f"/instructor/courses/{file_course.public_id}/files/{asset_id}/download"
        )
        assert dl_resp.status_code == 200
        assert dl_resp.data == doc_content
