"""REST API test suite for DOCX/PDF Assessment & Question Import Engine (TASK-020).

Validates:
- POST /api/courses/<course_id>/imports starts import job.
- GET /api/courses/<course_id>/imports lists import jobs for course.
- GET /api/imports/<job_id> retrieves job detail with extracted questions.
- POST /api/imports/<job_id>/process triggers parsing/dedup on demand.
- PATCH /api/imports/<job_id>/questions/<temp_id> edits question stem/choices.
- POST /api/imports/<job_id>/questions/<temp_id>/decision sets ACCEPTED/REJECTED.
- POST /api/imports/<job_id>/commit commits accepted questions to Question Bank.
- POST /api/imports/<job_id>/cancel cancels import job.
- Authentication & Authorization: 401 on unauthenticated, 403 on student or foreign instructor.
- Fail-closed security: 403 on quarantined/infected file.
- ADR-002: Zero internal BIGINT PK leakage.
"""

from __future__ import annotations

import io
import uuid
import zipfile

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course
from pwd301.models.file_import import FileAsset
from pwd301.models.identity import Role, User
from pwd301.models.question_bank import Question
from pwd301.services.course_service import create_course
from pwd301.services.file_service import store_file_stream
from pwd301.services.jwt_auth_service import create_token_pair
from pwd301.services.user_service import assign_role_to_user, register_user


def create_sample_docx(paragraphs: list[str]) -> bytes:
    """Generate in-memory valid OpenXML DOCX bytes."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        p_elements = "".join(f"<w:p><w:r><w:t>{p}</w:t></w:r></w:p>" for p in paragraphs)
        doc_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">\n'
            f"  <w:body>{p_elements}</w:body>\n"
            "</w:document>"
        )
        zf.writestr("word/document.xml", doc_xml.encode("utf-8"))
    return buffer.getvalue()


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
    """Create test instructor."""
    u = register_user(
        f"api_import_inst_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Import Inst"
    )
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def foreign_instructor(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create foreign instructor."""
    u = register_user(
        f"api_import_for_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Foreign Inst"
    )
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def student_user(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test student."""
    u = register_user(
        f"api_import_stu_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Import Student"
    )
    return assign_role_to_user(u.id, "STUDENT")


@pytest.fixture
def test_course(app: Flask, instructor_user: User) -> Course:
    """Create test course."""
    c = create_course(
        instructor_user,
        {
            "course_code": f"IMP-API-{uuid.uuid4().hex[:4].upper()}",
            "title": "DOCX Import API Test Course",
            "summary": "Import Summary",
        },
    )
    db.session.commit()
    return c


@pytest.fixture
def clean_docx_file_asset(instructor_user: User, test_course: Course) -> FileAsset:
    """Upload a clean DOCX file asset."""
    docx_bytes = create_sample_docx(
        [
            "Câu 1: Thủ đô của Việt Nam là thành phố nào?",
            "A. Hà Nội",
            "B. TP. Hồ Chí Minh",
            "C. Đà Nẵng",
            "D. Cần Thơ",
            "Đáp án: A",
            "Câu 2: Trình biên dịch GCC hỗ trợ ngôn ngữ C/C++.",
            "A. Đúng",
            "B. Sai",
            "Đáp án: Đúng",
        ]
    )
    asset = store_file_stream(
        actor=instructor_user,
        course_id=test_course.id,
        file_stream=io.BytesIO(docx_bytes),
        filename="questions_for_api.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        asset_type="IMPORT_SOURCE",
        session=db.session,
    )
    return asset


class TestImportRestApi:
    """REST API test suite for import engine."""

    def test_full_import_api_lifecycle(
        self,
        client: FlaskClient,
        instructor_user: User,
        test_course: Course,
        clean_docx_file_asset: FileAsset,
    ) -> None:
        """End-to-end import flow via REST endpoints."""
        tokens = create_token_pair(instructor_user)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # 1. Start import job
        create_resp = client.post(
            f"/api/courses/{test_course.public_id}/imports",
            headers=headers,
            json={
                "file_asset_id": str(clean_docx_file_asset.public_id),
                "auto_process": True,
            },
        )
        assert create_resp.status_code in (200, 201, 202)
        job_data = create_resp.get_json()
        job_id = job_data["id"]
        assert job_data["status"] == "REVIEW_REQUIRED"
        assert job_data["question_count"] == 2
        assert len(job_data["questions"]) == 2

        # 2. Get import job detail
        get_resp = client.get(f"/api/imports/{job_id}", headers=headers)
        assert get_resp.status_code == 200
        detail = get_resp.get_json()
        assert detail["id"] == job_id
        q1 = detail["questions"][0]
        q2 = detail["questions"][1]

        # ADR-002 check on public IDs
        assert "id" in q1
        assert uuid.UUID(q1["id"])
        assert "import_job_id" not in q1

        # 3. Patch question 1 content
        patch_resp = client.patch(
            f"/api/imports/{job_id}/questions/{q1['ordinal']}",
            headers=headers,
            json={"content": "Thủ đô chính thức của Việt Nam là gì?"},
        )
        assert patch_resp.status_code == 200
        patched_q = patch_resp.get_json()
        assert patched_q["content_text"] == "Thủ đô chính thức của Việt Nam là gì?"

        # 4. Set decisions: Accept Q1, Reject Q2
        dec_resp1 = client.post(
            f"/api/imports/{job_id}/questions/{q1['ordinal']}/decision",
            headers=headers,
            json={"action": "ACCEPTED"},
        )
        assert dec_resp1.status_code == 200

        dec_resp2 = client.post(
            f"/api/imports/{job_id}/questions/{q2['ordinal']}/decision",
            headers=headers,
            json={"action": "REJECTED"},
        )
        assert dec_resp2.status_code == 200

        # 5. Commit import
        commit_resp = client.post(f"/api/imports/{job_id}/commit", headers=headers)
        assert commit_resp.status_code == 200
        commit_data = commit_resp.get_json()
        assert commit_data["status"] == "COMPLETED"
        assert commit_data["imported_count"] == 1
        assert len(commit_data["created_question_ids"]) == 1

        # Verify Question in Question Bank
        created_qid = commit_data["created_question_ids"][0]
        created_q = (
            db.session.query(Question).filter(Question.public_id == uuid.UUID(created_qid)).first()
        )
        assert created_q is not None
        assert "Thủ đô chính thức" in created_q.current_revision.content

        # 6. Idempotency on commit: cannot commit again (409)
        commit_again = client.post(f"/api/imports/{job_id}/commit", headers=headers)
        assert commit_again.status_code == 409

    def test_list_course_imports_api(
        self,
        client: FlaskClient,
        instructor_user: User,
        test_course: Course,
        clean_docx_file_asset: FileAsset,
    ) -> None:
        """GET /api/courses/<course_id>/imports returns job list."""
        tokens = create_token_pair(instructor_user)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Create one job
        client.post(
            f"/api/courses/{test_course.public_id}/imports",
            headers=headers,
            json={"file_asset_id": str(clean_docx_file_asset.public_id), "auto_process": False},
        )

        resp = client.get(f"/api/courses/{test_course.public_id}/imports", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "items" in data
        assert len(data["items"]) >= 1
        assert "id" in data["items"][0]

    def test_cancel_import_job_api(
        self,
        client: FlaskClient,
        instructor_user: User,
        test_course: Course,
        clean_docx_file_asset: FileAsset,
    ) -> None:
        """POST /api/imports/<job_id>/cancel cancels the job."""
        tokens = create_token_pair(instructor_user)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        create_resp = client.post(
            f"/api/courses/{test_course.public_id}/imports",
            headers=headers,
            json={"file_asset_id": str(clean_docx_file_asset.public_id), "auto_process": False},
        )
        job_id = create_resp.get_json()["id"]

        cancel_resp = client.post(
            f"/api/imports/{job_id}/cancel",
            headers=headers,
            json={"reason": "User requested cancel"},
        )
        assert cancel_resp.status_code == 200
        cancel_data = cancel_resp.get_json()
        assert cancel_data["status"] == "CANCELLED"

    def test_api_unauthenticated_returns_401(
        self,
        client: FlaskClient,
        test_course: Course,
    ) -> None:
        """Unauthenticated requests must receive 401."""
        resp = client.post(f"/api/courses/{test_course.public_id}/imports", json={})
        assert resp.status_code == 401

    def test_api_student_returns_403(
        self,
        client: FlaskClient,
        student_user: User,
        test_course: Course,
        clean_docx_file_asset: FileAsset,
    ) -> None:
        """Students must receive 403 on import endpoints."""
        tokens = create_token_pair(student_user)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        resp = client.post(
            f"/api/courses/{test_course.public_id}/imports",
            headers=headers,
            json={"file_asset_id": str(clean_docx_file_asset.public_id)},
        )
        assert resp.status_code == 403

    def test_api_foreign_instructor_returns_403(
        self,
        client: FlaskClient,
        foreign_instructor: User,
        test_course: Course,
        clean_docx_file_asset: FileAsset,
    ) -> None:
        """Instructors not managing the course must receive 403."""
        tokens = create_token_pair(foreign_instructor)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        resp = client.post(
            f"/api/courses/{test_course.public_id}/imports",
            headers=headers,
            json={"file_asset_id": str(clean_docx_file_asset.public_id)},
        )
        assert resp.status_code == 403

    def test_api_quarantined_file_returns_403(
        self,
        client: FlaskClient,
        instructor_user: User,
        test_course: Course,
        clean_docx_file_asset: FileAsset,
    ) -> None:
        """Quarantined files must receive 403 FILE_QUARANTINED."""
        assert clean_docx_file_asset.current_revision is not None
        clean_docx_file_asset.current_revision.status = "QUARANTINED"
        db.session.commit()

        tokens = create_token_pair(instructor_user)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        resp = client.post(
            f"/api/courses/{test_course.public_id}/imports",
            headers=headers,
            json={"file_asset_id": str(clean_docx_file_asset.public_id)},
        )
        assert resp.status_code == 403

    def test_direct_api_imports_and_process_endpoint(
        self,
        client: FlaskClient,
        instructor_user: User,
        test_course: Course,
        clean_docx_file_asset: FileAsset,
    ) -> None:
        """POST /api/imports directly and trigger POST /api/imports/<job_id>/process."""
        tokens = create_token_pair(instructor_user)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # 1. Create with auto_process = False
        resp = client.post(
            "/api/imports",
            headers=headers,
            json={
                "course_id": str(test_course.public_id),
                "file_asset_id": str(clean_docx_file_asset.public_id),
                "auto_process": False,
            },
        )
        assert resp.status_code == 202
        job_data = resp.get_json()
        job_id = job_data["id"]
        assert job_data["status"] == "QUEUED"

        # 2. Trigger process endpoint
        proc_resp = client.post(f"/api/imports/{job_id}/process", headers=headers)
        assert proc_resp.status_code == 200
        proc_data = proc_resp.get_json()
        assert proc_data["status"] == "REVIEW_REQUIRED"
        assert proc_data["question_count"] == 2

    def test_instructor_web_portal_import_routes(
        self,
        client: FlaskClient,
        instructor_user: User,
        test_course: Course,
        clean_docx_file_asset: FileAsset,
    ) -> None:
        """Instructor web portal session-based routes with CSRF protection."""
        from tests.conftest import login_web_user

        login_web_user(client, instructor_user)

        # 1. Create import job via instructor portal
        resp = client.post(
            f"/instructor/courses/{test_course.public_id}/imports",
            json={
                "file_asset_id": str(clean_docx_file_asset.public_id),
                "auto_process": True,
            },
        )
        assert resp.status_code in (201, 202)
        job_data = resp.get_json()
        job_id = job_data["id"]
        assert job_data["status"] == "REVIEW_REQUIRED"

        # 2. View details
        det_resp = client.get(f"/instructor/imports/{job_id}")
        assert det_resp.status_code == 200
        det_data = det_resp.get_json()
        assert det_data["id"] == job_id

        # 3. Accept question 1
        dec_resp = client.post(
            f"/instructor/imports/{job_id}/questions/1/decision",
            json={"action": "ACCEPTED"},
        )
        assert dec_resp.status_code == 200

        # 4. Commit via instructor portal
        com_resp = client.post(f"/instructor/imports/{job_id}/commit")
        assert com_resp.status_code == 200
        com_data = com_resp.get_json()
        assert com_data["status"] == "COMPLETED"
        assert com_data["imported_count"] == 1
