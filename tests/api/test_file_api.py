"""Integration tests for File REST API and Web Instructor routes."""

from __future__ import annotations

import io
import uuid

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course, Lesson
from pwd301.models.identity import Role, User
from pwd301.services.course_service import create_course
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.lesson_service import create_lesson
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
def instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test instructor user."""
    u = register_user("api_file_inst@example.com", "Password@123", "API File Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def other_instructor_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create secondary instructor user."""
    u = register_user("api_file_other_inst@example.com", "Password@123", "Other Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test student user."""
    return register_user("api_file_stu@example.com", "Password@123", "API File Student")


@pytest.fixture
def admin_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test admin user."""
    u = register_user("api_file_adm@example.com", "Password@123", "API File Admin")
    return assign_role_to_user(u.id, "ADMIN")


@pytest.fixture
def test_course(app: Flask, instructor_user: User) -> Course:
    """Create test course managed by instructor_user."""
    c = create_course(
        instructor_user,
        {
            "course_code": f"FILE-{uuid.uuid4().hex[:4].upper()}",
            "title": "File Systems & Security",
            "category": "Computer Science",
            "difficulty": "INTERMEDIATE",
        },
    )
    c.status = "PUBLISHED"
    db.session.commit()
    return c


@pytest.fixture
def test_lesson(app: Flask, instructor_user: User, test_course: Course) -> Lesson:
    """Create test lesson in test_course."""
    lesson = create_lesson(
        instructor_user,
        str(test_course.public_id),
        {
            "title": "File Storage Foundations",
            "position": 1,
            "markdown_content": "# File Storage Lesson Content",
        },
        session=db.session,
    )
    lesson.status = "PUBLISHED"
    db.session.commit()
    return lesson


class TestFileApiEndpoints:
    """REST API integration test suite for /api/files and /api/courses/<id>/files."""

    def test_upload_file_rest_api_success(
        self, client: FlaskClient, instructor_user: User, test_course: Course
    ) -> None:
        """POST /api/courses/<course_id>/files uploads file and returns 201 with public UUID."""
        tokens = create_token_pair(instructor_user)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        file_data = (io.BytesIO(b"%PDF-1.4 sample PDF content for testing"), "lecture_slides.pdf")
        resp = client.post(
            f"/api/courses/{test_course.public_id}/files",
            data={"file": file_data, "title": "Lecture 1 Slides"},
            content_type="multipart/form-data",
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["title"] == "Lecture 1 Slides"
        assert data["original_filename"] == "lecture_slides.pdf"
        assert data["mime_type"] == "application/pdf"
        assert data["status"] == "ACTIVE"
        assert data["current_version"] == 1
        assert "asset_id" in data
        # Check UUID format
        uuid.UUID(data["asset_id"])
        # Invariant: No BIGINT PK leaked
        assert "id" not in data
        assert "blob_id" not in data
        assert "storage_path" not in data

    def test_upload_dangerous_extension_rejected(
        self, client: FlaskClient, instructor_user: User, test_course: Course
    ) -> None:
        """POST /api/courses/<course_id>/files rejects dangerous extensions with 400."""
        tokens = create_token_pair(instructor_user)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        file_data = (io.BytesIO(b"malicious script"), "payload.exe")
        resp = client.post(
            f"/api/courses/{test_course.public_id}/files",
            data={"file": file_data},
            content_type="multipart/form-data",
            headers=headers,
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_list_and_get_metadata_rest_api(
        self, client: FlaskClient, instructor_user: User, test_course: Course
    ) -> None:
        """GET /api/courses/<id>/files and GET /api/files/<id> return serialized assets."""
        tokens = create_token_pair(instructor_user)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Upload two files
        for i in range(2):
            client.post(
                f"/api/courses/{test_course.public_id}/files",
                data={"file": (io.BytesIO(f"test content {i}".encode()), f"test_{i}.txt")},
                content_type="multipart/form-data",
                headers=headers,
            )

        # List
        list_resp = client.get(f"/api/courses/{test_course.public_id}/files", headers=headers)
        assert list_resp.status_code == 200
        items = list_resp.get_json()["items"]
        assert len(items) == 2
        asset_id = items[0]["asset_id"]

        # Get metadata
        meta_resp = client.get(f"/api/files/{asset_id}", headers=headers)
        assert meta_resp.status_code == 200
        meta = meta_resp.get_json()
        assert meta["asset_id"] == asset_id
        assert len(meta["revisions"]) == 1
        assert meta["revisions"][0]["version"] == 1

    def test_download_rest_api_headers_and_content(
        self, client: FlaskClient, instructor_user: User, test_course: Course
    ) -> None:
        """GET /api/files/<asset_id>/download streams content with defensive headers."""
        tokens = create_token_pair(instructor_user)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        raw_content = b"%PDF-1.4 binary content stream for verification"
        upload_resp = client.post(
            f"/api/courses/{test_course.public_id}/files",
            data={"file": (io.BytesIO(raw_content), "secure_handout.pdf")},
            content_type="multipart/form-data",
            headers=headers,
        )
        assert upload_resp.status_code == 201
        asset_id = upload_resp.get_json()["asset_id"]

        # Download
        dl_resp = client.get(f"/api/files/{asset_id}/download", headers=headers)
        assert dl_resp.status_code == 200
        assert dl_resp.data == raw_content
        assert dl_resp.headers["X-Content-Type-Options"] == "nosniff"
        assert 'filename="secure_handout.pdf"' in dl_resp.headers["Content-Disposition"]

    def test_add_revision_and_versioned_download(
        self, client: FlaskClient, instructor_user: User, test_course: Course
    ) -> None:
        """POST /api/files/<id>/revisions adds a new version and supports versioned download."""
        tokens = create_token_pair(instructor_user)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        v1_content = b"Content Version 1.0"
        upload_resp = client.post(
            f"/api/courses/{test_course.public_id}/files",
            data={"file": (io.BytesIO(v1_content), "notes.txt")},
            content_type="multipart/form-data",
            headers=headers,
        )
        asset_id = upload_resp.get_json()["asset_id"]

        # Add revision
        v2_content = b"Content Version 2.0 with updates"
        rev_resp = client.post(
            f"/api/files/{asset_id}/revisions",
            data={"file": (io.BytesIO(v2_content), "notes.txt"), "change_summary": "Updated notes"},
            content_type="multipart/form-data",
            headers=headers,
        )
        assert rev_resp.status_code == 201
        rev_data = rev_resp.get_json()
        assert rev_data["current_version"] == 2
        assert len(rev_data["revisions"]) == 2

        # Download latest (should be v2)
        dl_latest = client.get(f"/api/files/{asset_id}/download", headers=headers)
        assert dl_latest.status_code == 200
        assert dl_latest.data == v2_content

        # Download v1
        dl_v1 = client.get(f"/api/files/{asset_id}/download?version=1", headers=headers)
        assert dl_v1.status_code == 200
        assert dl_v1.data == v1_content

    def test_soft_delete_and_restore_rest_api(
        self, client: FlaskClient, instructor_user: User, test_course: Course
    ) -> None:
        """DELETE /api/files/<asset_id> trashes file and POST /restore recovers it."""
        tokens = create_token_pair(instructor_user)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        upload_resp = client.post(
            f"/api/courses/{test_course.public_id}/files",
            data={"file": (io.BytesIO(b"Doc content"), "syllabus.pdf")},
            content_type="multipart/form-data",
            headers=headers,
        )
        asset_id = upload_resp.get_json()["asset_id"]

        # Delete (trash)
        del_resp = client.delete(f"/api/files/{asset_id}", headers=headers)
        assert del_resp.status_code == 200
        assert del_resp.get_json()["status"] == "TRASH"

        # Restore
        res_resp = client.post(f"/api/files/{asset_id}/restore", headers=headers)
        assert res_resp.status_code == 200
        assert res_resp.get_json()["status"] == "ACTIVE"

    def test_lesson_resource_attach_and_detach_rest_api(
        self, client: FlaskClient, instructor_user: User, test_course: Course, test_lesson: Lesson
    ) -> None:
        """POST /api/lessons/<lesson_id>/resources and DELETE /resources/<resource_id> lifecycle."""
        tokens = create_token_pair(instructor_user)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Upload asset first
        upload_resp = client.post(
            f"/api/courses/{test_course.public_id}/files",
            data={"file": (io.BytesIO(b"Lesson lab file"), "lab1.pdf")},
            content_type="multipart/form-data",
            headers=headers,
        )
        asset_id = upload_resp.get_json()["asset_id"]

        # Attach to lesson
        attach_resp = client.post(
            f"/api/lessons/{test_lesson.public_id}/resources",
            json={"file_asset_id": asset_id, "title": "Lab 1 Manual"},
            headers=headers,
        )
        assert attach_resp.status_code == 201
        res_data = attach_resp.get_json()
        assert res_data["title"] == "Lab 1 Manual"
        resource_id = res_data["resource_id"]

        # Detach
        detach_resp = client.delete(
            f"/api/lessons/{test_lesson.public_id}/resources/{resource_id}",
            headers=headers,
        )
        assert detach_resp.status_code == 200
        assert detach_resp.get_json()["detached"] is True


class TestWebInstructorFileRoutes:
    """Test suite for Web UI / Instructor session-authenticated file endpoints."""

    def test_web_instructor_upload_and_list(
        self, client: FlaskClient, instructor_user: User, test_course: Course
    ) -> None:
        """Instructor uploads file via Web session and views course file listing."""
        login_web_user(client, instructor_user)

        # Upload file via web route
        resp = client.post(
            f"/instructor/courses/{test_course.public_id}/files",
            data={
                "file": (io.BytesIO(b"Web upload content"), "web_guide.pdf"),
                "title": "Web Guide",
            },
            content_type="multipart/form-data",
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["title"] == "Web Guide"
        asset_id = data["asset_id"]

        # List files via web route
        list_resp = client.get(
            f"/instructor/courses/{test_course.public_id}/files",
            headers={"Accept": "application/json"},
        )
        assert list_resp.status_code == 200
        files = list_resp.get_json()["items"]
        assert any(f["asset_id"] == asset_id for f in files)

    def test_web_instructor_trash_and_restore(
        self, client: FlaskClient, instructor_user: User, test_course: Course
    ) -> None:
        """Instructor trashes and restores a file via Web session."""
        login_web_user(client, instructor_user)

        # Upload
        up_resp = client.post(
            f"/instructor/courses/{test_course.public_id}/files",
            data={"file": (io.BytesIO(b"To be trashed"), "trash_me.txt")},
            content_type="multipart/form-data",
            headers={"Accept": "application/json"},
        )
        asset_id = up_resp.get_json()["asset_id"]

        # Trash
        trash_resp = client.post(
            f"/instructor/files/{asset_id}/trash",
            headers={"Accept": "application/json"},
        )
        assert trash_resp.status_code == 200
        assert trash_resp.get_json()["status"] == "TRASH"

        # Restore
        restore_resp = client.post(
            f"/instructor/files/{asset_id}/restore",
            headers={"Accept": "application/json"},
        )
        assert restore_resp.status_code == 200
        assert restore_resp.get_json()["status"] == "ACTIVE"
