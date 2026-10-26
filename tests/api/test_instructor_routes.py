"""Integration & API Tests for Instructor Routes, Attachment Hardening, and Resource Preservation.

Verifies:
1. Strict Non-Archive Policy: .zip, .rar, .7z, .tar, .gz, etc. are rejected with HTTP 400 and exact Vietnamese error message.
2. Magic byte archive inspection: generic zip archives disguised as .pdf or .docx are rejected.
3. AutoCAD and 3D formats (.dwg, .dxf, .obj, .fbx, .stl, .blend, .step, .stp, .gltf, .glb) are accepted with HTTP 201.
4. Strict 50MB ceiling (> 50,000,000 bytes rejected).
5. Staged lesson resource preservation: uploading an attachment to a published lesson creates a staged draft lesson,
   and subsequent text autosave does NOT soft-delete the draft because is_identical recognizes the resource difference.
"""

from __future__ import annotations

import io
import uuid
import zipfile
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from backend.extensions import db
from backend.models.course import Lesson
from backend.seeds.baseline import seed_baseline
from backend.services.course_service import create_course
from backend.services.lesson_service import create_lesson
from backend.services.user_service import assign_role_to_user, register_user

FORBIDDEN_ARCHIVE_MESSAGE = (
    "Hệ thống không hỗ trợ tệp nén (.zip, .rar, .7z...). Vui lòng tải trực tiếp tài liệu học tập (PDF, Word, Excel, CAD, 3D...)"
)


@pytest.fixture
def instructor_env(app: Flask) -> dict[str, Any]:
    """Setup instructor and published course with an initial lesson."""
    sess: Session = db.session
    seed_baseline(sess)

    inst_user = register_user(
        email=f"inst_upload_{uuid.uuid4().hex[:8]}@backend.local",
        password="Password@123",
        display_name="Giảng Viên Kiểm Thử",
        session=sess,
    )
    assign_role_to_user(inst_user.id, "INSTRUCTOR", session=sess)

    course = create_course(
        actor=inst_user,
        data={
            "course_code": f"CAD-{uuid.uuid4().hex[:4].upper()}",
            "title": "Thiết Kế Đồ Họa và Mô Hình 3D",
            "category": "Architecture",
            "capacity": 40,
        },
        session=sess,
    )

    lesson = create_lesson(
        actor=inst_user,
        course_id=course.id,
        data={
            "title": "Bài 01: Nhập môn AutoCAD và Phối cảnh",
            "markdown_content": "# Nội dung bài giảng gốc",
            "estimated_duration_minutes": 45,
            "status": "PUBLISHED",
        },
        session=sess,
    )
    lesson.status = "PUBLISHED"
    course.status = "PUBLISHED"
    sess.commit()

    return {
        "instructor": inst_user,
        "course": course,
        "lesson": lesson,
    }


def login_client(client: FlaskClient, email: str, password: str = "Password@123") -> str:
    """Log in instructor and return CSRF token."""
    res = client.post("/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed: {res.get_json()}"
    return res.get_json().get("csrf_token", "")


def test_instructor_upload_archive_rejected_with_exact_vietnamese_message(
    client: FlaskClient, instructor_env: dict[str, Any]
) -> None:
    """Canonical invariant: uploading archive extensions returns HTTP 400 and exact Vietnamese error."""
    inst = instructor_env["instructor"]
    course = instructor_env["course"]
    lesson = instructor_env["lesson"]

    csrf = login_client(client, inst.email)

    archive_extensions = [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso"]
    for ext in archive_extensions:
        filename = f"archive{ext}"
        payload = {
            "file": (io.BytesIO(b"Fake compressed archive content"), filename),
            "label": "Tệp nén bài tập",
        }
        res = client.post(
            f"/instructor/courses/{course.public_id}/lessons/{lesson.public_id}/resources",
            data=payload,
            content_type="multipart/form-data",
            headers={"X-CSRF-Token": csrf},
        )
        assert res.status_code == 400, f"Expected 400 for {filename}, got {res.status_code}: {res.get_json()}"
        data = res.get_json()
        assert data.get("success") is False
        err_msg = data.get("error", {}).get("message") if isinstance(data.get("error"), dict) else data.get("error")
        assert err_msg == FORBIDDEN_ARCHIVE_MESSAGE


def test_instructor_upload_archive_magic_bytes_rejected(
    client: FlaskClient, instructor_env: dict[str, Any]
) -> None:
    """Canonical invariant: archive magic bytes are rejected even when masqueraded as pdf/docx."""
    inst = instructor_env["instructor"]
    course = instructor_env["course"]
    lesson = instructor_env["lesson"]

    csrf = login_client(client, inst.email)

    # 1. Plain ZIP container masqueraded as PDF
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as zf:
        zf.writestr("notes.txt", b"secret materials")
    zip_bytes = zip_buf.getvalue()

    res_pdf = client.post(
        f"/instructor/courses/{course.public_id}/lessons/{lesson.public_id}/resources",
        data={"file": (io.BytesIO(zip_bytes), "disguised.pdf")},
        content_type="multipart/form-data",
        headers={"X-CSRF-Token": csrf},
    )
    assert res_pdf.status_code == 400, f"Expected 400, got {res_pdf.status_code}"
    err_pdf = res_pdf.get_json().get("error", {}).get("message") if isinstance(res_pdf.get_json().get("error"), dict) else res_pdf.get_json().get("error")
    assert err_pdf == FORBIDDEN_ARCHIVE_MESSAGE

    # 2. Generic ZIP container masqueraded as DOCX (lacks [Content_Types].xml and word/ tree)
    res_docx = client.post(
        f"/instructor/courses/{course.public_id}/lessons/{lesson.public_id}/resources",
        data={"file": (io.BytesIO(zip_bytes), "fake_doc.docx")},
        content_type="multipart/form-data",
        headers={"X-CSRF-Token": csrf},
    )
    assert res_docx.status_code == 400, f"Expected 400, got {res_docx.status_code}"
    err_docx = res_docx.get_json().get("error", {}).get("message") if isinstance(res_docx.get_json().get("error"), dict) else res_docx.get_json().get("error")
    assert err_docx == FORBIDDEN_ARCHIVE_MESSAGE


def test_instructor_upload_cad_and_3d_files_accepted(
    client: FlaskClient, instructor_env: dict[str, Any]
) -> None:
    """Verify AutoCAD and 3D files (.dwg, .dxf, .obj, .fbx, .stl, .blend, .step, .glb) are accepted with HTTP 201."""
    inst = instructor_env["instructor"]
    course = instructor_env["course"]

    csrf = login_client(client, inst.email)

    cad_3d_files = [
        ("floorplan.dwg", b"AC1027\x00\x00AutoCAD drawing payload"),
        ("details.dxf", b"SECTION\n  2\nHEADER\n  0\nENDSEC\n  0\nEOF\n"),
        ("chair.obj", b"v 0.0 0.0 0.0\nv 1.0 1.0 1.0\nf 1 2 3\n"),
        ("model.fbx", b"Kaydara FBX Binary  \x00Payload"),
        ("bracket.stl", b"solid bracket\n  facet normal 0 0 0\n  endfacet\nendsolid bracket\n"),
        ("scene.blend", b"BLENDER_v300ScenePayload"),
        ("part.step", b"ISO-10303-21;\nHEADER;\nENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;\n"),
        ("assembly.stp", b"ISO-10303-21;\nHEADER;\nENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;\n"),
        ("asset.gltf", b'{"asset": {"version": "2.0"}, "nodes": []}'),
        ("asset.glb", b"glTF\x02\x00\x00\x00\x0c\x00\x00\x00BinaryPayload"),
    ]

    target_lesson = None
    for idx, (filename, content) in enumerate(cad_3d_files):
        # A lesson can contain at most 5 documents; create a new lesson every 5 files
        if idx % 5 == 0:
            target_lesson = create_lesson(
                actor=inst,
                course_id=course.id,
                data={
                    "title": f"Bài thực hành CAD/3D {idx // 5 + 1}",
                    "markdown_content": "# Nội dung CAD/3D",
                    "estimated_duration_minutes": 30,
                    "status": "PUBLISHED",
                },
                session=db.session,
            )
            target_lesson.status = "PUBLISHED"
            db.session.commit()

        res = client.post(
            f"/instructor/courses/{course.public_id}/lessons/{target_lesson.public_id}/resources",
            data={"file": (io.BytesIO(content), filename), "label": filename},
            content_type="multipart/form-data",
            headers={"X-CSRF-Token": csrf},
        )
        assert res.status_code == 201, f"Failed to upload {filename}: {res.status_code} - {res.get_json()}"
        data = res.get_json()
        assert data.get("resource_id") is not None
        assert data.get("filename") == filename
        # Ensure lesson_id is returned
        assert data.get("lesson_id") is not None


def test_instructor_upload_over_50mb_rejected(
    client: FlaskClient, instructor_env: dict[str, Any]
) -> None:
    """Verify strict 50MB ceiling rejection on upload (> 50,000,000 bytes)."""
    inst = instructor_env["instructor"]
    course = instructor_env["course"]
    lesson = instructor_env["lesson"]

    csrf = login_client(client, inst.email)

    class OversizedBytesIO(io.BytesIO):
        """Simulate an oversized 50,000,001-byte file stream without consuming RAM."""
        def __init__(self, size: int) -> None:
            super().__init__()
            self._size = size
            self._pos = 0

        def read(self, size: int = -1) -> bytes:
            if self._pos >= self._size:
                return b""
            chunk_len = min(size if size > 0 else 65536, self._size - self._pos)
            self._pos += chunk_len
            return b"A" * chunk_len

        def seek(self, offset: int, whence: int = 0) -> int:
            if whence == 0:
                self._pos = offset
            elif whence == 1:
                self._pos += offset
            elif whence == 2:
                self._pos = self._size + offset
            return self._pos

        def tell(self) -> int:
            return self._pos

    oversized_file = OversizedBytesIO(50_000_001)
    res = client.post(
        f"/instructor/courses/{course.public_id}/lessons/{lesson.public_id}/resources",
        data={"file": (oversized_file, "oversized.pdf")},
        content_type="multipart/form-data",
        headers={"X-CSRF-Token": csrf},
    )
    # Payload too large yields HTTP 413 or 400
    assert res.status_code in (413, 400), f"Expected 413/400 for >50MB upload, got {res.status_code}: {res.get_json()}"


def test_staged_lesson_resource_upload_preservation(
    client: FlaskClient, instructor_env: dict[str, Any]
) -> None:
    """Verify staged draft lesson is NOT soft-deleted by subsequent text autosave when resources differ."""
    inst = instructor_env["instructor"]
    course = instructor_env["course"]
    lesson = instructor_env["lesson"]

    csrf = login_client(client, inst.email)

    # 1. Upload a resource to the published lesson (creates a staged draft lesson)
    res_upload = client.post(
        f"/instructor/courses/{course.public_id}/lessons/{lesson.public_id}/resources",
        data={"file": (io.BytesIO(b"%PDF-1.4\nEducational Document Handout\n%%EOF"), "handout.pdf")},
        content_type="multipart/form-data",
        headers={"X-CSRF-Token": csrf},
    )
    assert res_upload.status_code == 201, f"Upload failed: {res_upload.get_json()}"
    upload_data = res_upload.get_json()
    staged_lesson_public_id = upload_data.get("lesson_id")
    assert staged_lesson_public_id is not None

    # Query DB to find the staged draft lesson
    staged_lesson = (
        db.session.query(Lesson)
        .filter(Lesson.public_id == uuid.UUID(staged_lesson_public_id))
        .first()
    )
    assert staged_lesson is not None
    assert staged_lesson.status == "DRAFT"
    assert staged_lesson.deleted_at is None
    assert len(staged_lesson.resources) >= 1

    # 2. Simulate client autosave with unmodified text fields targeting the original live lesson ID
    res_autosave = client.put(
        f"/instructor/lessons/{lesson.public_id}",
        json={
            "title": lesson.title,
            "markdown_content": lesson.markdown_content,
            "summary": lesson.summary,
            "estimated_duration_minutes": lesson.estimated_duration_minutes,
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert res_autosave.status_code == 200, f"Autosave failed: {res_autosave.get_json()}"
    autosave_data = res_autosave.get_json()

    # The staged lesson must NOT be marked deleted because has_resource_diff is True!
    db.session.refresh(staged_lesson)
    assert staged_lesson.deleted_at is None, "Staged draft lesson was erroneously soft-deleted!"
    assert len(staged_lesson.resources) >= 1, "Attached resource was lost!"
    assert autosave_data.get("is_draft") is True
