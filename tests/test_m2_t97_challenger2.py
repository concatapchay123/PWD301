"""Empirical Challenge Test Suite for Milestone 2 (Challenger 2).

Systematic verification of:
- Challenge 1: Uploading a raw .zip file renamed to .docx or .pdf must be rejected with the exact Vietnamese error message.
- Challenge 2: Uploading an attachment of size 50,000,001 bytes must be rejected (HTTP 413 or validation error).
- Challenge 3: In staging state, uploading an attachment to a published lesson creates a staged draft,
  and immediately sending a text update with identical title/content must NOT delete the staged draft lesson or its resource.
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

from pwd301.extensions import db
from pwd301.models.course import Lesson
from pwd301.seeds.baseline import seed_baseline
from pwd301.services.course_service import create_course
from pwd301.services.exceptions import (
    FileSizeLimitExceededError,
    FileValidationError,
)
from pwd301.services.file_service import (
    LimitingStream,
    check_file_size_limit,
    store_file_stream,
)
from pwd301.services.lesson_service import create_lesson
from pwd301.services.user_service import assign_role_to_user, register_user

EXPECTED_VIETNAMESE_REJECTION = (
    "Hệ thống không hỗ trợ tệp nén (.zip, .rar, .7z...). Vui lòng tải trực tiếp tài liệu học tập (PDF, Word, Excel, CAD, 3D...)"
)


@pytest.fixture
def instructor_fixture(app: Flask) -> dict[str, Any]:
    """Provision baseline instructor and published course with a published lesson."""
    sess: Session = db.session
    seed_baseline(sess)

    inst = register_user(
        email=f"inst_challenger_{uuid.uuid4().hex[:8]}@pwd301.local",
        password="Password@123",
        display_name="Giảng Viên Thẩm Định",
        session=sess,
    )
    assign_role_to_user(inst.id, "INSTRUCTOR", session=sess)

    course = create_course(
        actor=inst,
        data={
            "course_code": f"CHAL-{uuid.uuid4().hex[:4].upper()}",
            "title": "Khóa Học Thẩm Định Đính Kèm",
            "category": "Architecture & Engineering",
            "capacity": 50,
        },
        session=sess,
    )

    lesson = create_lesson(
        actor=inst,
        course_id=course.id,
        data={
            "title": "Bài 01: Kiến Trúc Nền Tảng",
            "markdown_content": "# Nội dung bài giảng kiến trúc nền tảng\nChi tiết bài học.",
            "summary": "Tóm tắt bài 01",
            "estimated_duration_minutes": 45,
            "status": "PUBLISHED",
        },
        session=sess,
    )
    lesson.status = "PUBLISHED"
    course.status = "PUBLISHED"
    sess.commit()

    return {
        "instructor": inst,
        "course": course,
        "lesson": lesson,
    }


def login_instructor(client: FlaskClient, email: str, password: str = "Password@123") -> str:
    """Log in instructor and return the CSRF token."""
    res = client.post("/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed: {res.get_json()}"
    return res.get_json().get("csrf_token", "")


# ==============================================================================
# CHALLENGE 1: Disguised Archive Inspection & Exact Vietnamese Error Message
# ==============================================================================


class TestChallenge1DisguisedArchiveInspection:
    """Verify raw .zip or other archives disguised as .docx/.pdf are rejected with the canonical message."""

    def test_zip_disguised_as_docx_rejected_at_api_level(
        self, client: FlaskClient, instructor_fixture: dict[str, Any]
    ) -> None:
        """Uploading a raw .zip file renamed to .docx must return HTTP 400 and the exact message."""
        inst = instructor_fixture["instructor"]
        course = instructor_fixture["course"]
        lesson = instructor_fixture["lesson"]
        csrf = login_instructor(client, inst.email)

        # Create a raw ZIP container with arbitrary files (no OOXML structure)
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            zf.writestr("notes.txt", b"secret exam notes")
            zf.writestr("data.bin", b"\x00\x01\x02\x03")
        disguised_zip_bytes = zip_buf.getvalue()

        res = client.post(
            f"/instructor/courses/{course.public_id}/lessons/{lesson.public_id}/resources",
            data={"file": (io.BytesIO(disguised_zip_bytes), "syllabus.docx"), "label": "Tài liệu giáo trình"},
            content_type="multipart/form-data",
            headers={"X-CSRF-Token": csrf},
        )
        assert res.status_code == 400, f"Expected HTTP 400, got {res.status_code}: {res.get_json()}"
        data = res.get_json()
        assert data.get("success") is False
        err = data.get("error", {}).get("message") if isinstance(data.get("error"), dict) else data.get("error")
        assert err == EXPECTED_VIETNAMESE_REJECTION

    def test_zip_disguised_as_pdf_rejected_at_api_level(
        self, client: FlaskClient, instructor_fixture: dict[str, Any]
    ) -> None:
        """Uploading a raw .zip file renamed to .pdf must return HTTP 400 and the exact message."""
        inst = instructor_fixture["instructor"]
        course = instructor_fixture["course"]
        lesson = instructor_fixture["lesson"]
        csrf = login_instructor(client, inst.email)

        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            zf.writestr("archive.txt", b"nested data archive")
        disguised_zip_bytes = zip_buf.getvalue()

        res = client.post(
            f"/instructor/courses/{course.public_id}/lessons/{lesson.public_id}/resources",
            data={"file": (io.BytesIO(disguised_zip_bytes), "handout.pdf"), "label": "Tài liệu tham khảo"},
            content_type="multipart/form-data",
            headers={"X-CSRF-Token": csrf},
        )
        assert res.status_code == 400, f"Expected HTTP 400, got {res.status_code}: {res.get_json()}"
        data = res.get_json()
        assert data.get("success") is False
        err = data.get("error", {}).get("message") if isinstance(data.get("error"), dict) else data.get("error")
        assert err == EXPECTED_VIETNAMESE_REJECTION

    def test_zip_disguised_as_docx_and_pdf_at_service_level(
        self, instructor_fixture: dict[str, Any]
    ) -> None:
        """Service store_file_stream must raise FileValidationError with the exact Vietnamese message."""
        inst = instructor_fixture["instructor"]
        course = instructor_fixture["course"]

        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            zf.writestr("file.txt", b"plain text inside zip")
        zip_payload = zip_buf.getvalue()

        for filename in ["fake.docx", "fake.pdf"]:
            with pytest.raises(FileValidationError) as exc_info:
                store_file_stream(
                    actor=inst,
                    course_id=course.public_id,
                    file_stream=io.BytesIO(zip_payload),
                    filename=filename,
                    session=db.session,
                )
            assert str(exc_info.value) == EXPECTED_VIETNAMESE_REJECTION

    def test_empty_zip_disguised_as_docx_or_pdf_rejected(
        self, client: FlaskClient, instructor_fixture: dict[str, Any]
    ) -> None:
        """An empty zip file (starts with PK\\x05\\x06) renamed to .docx or .pdf must be rejected."""
        inst = instructor_fixture["instructor"]
        course = instructor_fixture["course"]
        lesson = instructor_fixture["lesson"]
        csrf = login_instructor(client, inst.email)

        # Empty zip file structure: 22 bytes end of central directory record
        empty_zip_bytes = b"PK\x05\x06" + b"\x00" * 18

        for filename in ["empty.docx", "empty.pdf"]:
            res = client.post(
                f"/instructor/courses/{course.public_id}/lessons/{lesson.public_id}/resources",
                data={"file": (io.BytesIO(empty_zip_bytes), filename), "label": filename},
                content_type="multipart/form-data",
                headers={"X-CSRF-Token": csrf},
            )
            assert res.status_code == 400, f"Expected HTTP 400 for {filename}, got {res.status_code}"
            err = res.get_json().get("error", {}).get("message") if isinstance(res.get_json().get("error"), dict) else res.get_json().get("error")
            assert err == EXPECTED_VIETNAMESE_REJECTION

    def test_rar_7z_tar_gz_disguised_rejected_with_exact_message(
        self, client: FlaskClient, instructor_fixture: dict[str, Any]
    ) -> None:
        """Other forbidden archive types disguised as documents or CAD files must be rejected."""
        inst = instructor_fixture["instructor"]
        course = instructor_fixture["course"]
        lesson = instructor_fixture["lesson"]
        csrf = login_instructor(client, inst.email)

        disguised_archives = [
            ("disguised_rar.pdf", b"Rar!\x1a\x07\x00\x00\x00\x00PayloadRAR4"),
            ("disguised_rar5.docx", b"Rar!\x1a\x07\x01\x00\x00\x00PayloadRAR5"),
            ("disguised_7z.dwg", b"7z\xbc\xaf\x27\x1c\x00\x00Payload7Zip"),
            ("disguised_gz.pdf", b"\x1f\x8b\x08\x00\x00\x00\x00\x00GzipPayload"),
            ("disguised_bz2.docx", b"BZh91AY&SY\x00\x00Bzip2Payload"),
            ("disguised_xz.obj", b"\xfd7zXZ\x00\x00XZPayload"),
        ]

        for filename, payload in disguised_archives:
            res = client.post(
                f"/instructor/courses/{course.public_id}/lessons/{lesson.public_id}/resources",
                data={"file": (io.BytesIO(payload), filename), "label": filename},
                content_type="multipart/form-data",
                headers={"X-CSRF-Token": csrf},
            )
            assert res.status_code == 400, f"Expected 400 for {filename}, got {res.status_code}"
            err = res.get_json().get("error", {}).get("message") if isinstance(res.get_json().get("error"), dict) else res.get_json().get("error")
            assert err == EXPECTED_VIETNAMESE_REJECTION

    def test_genuine_pdf_accepted(
        self, client: FlaskClient, instructor_fixture: dict[str, Any]
    ) -> None:
        """Genuine PDF must pass validation with HTTP 201."""
        inst = instructor_fixture["instructor"]
        course = instructor_fixture["course"]
        lesson = instructor_fixture["lesson"]
        csrf = login_instructor(client, inst.email)

        pdf_bytes = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
        res_pdf = client.post(
            f"/instructor/courses/{course.public_id}/lessons/{lesson.public_id}/resources",
            data={"file": (io.BytesIO(pdf_bytes), "genuine.pdf"), "label": "Giáo trình PDF"},
            content_type="multipart/form-data",
            headers={"X-CSRF-Token": csrf},
        )
        assert res_pdf.status_code == 201, f"Genuine PDF rejected: {res_pdf.get_json()}"

    def test_genuine_docx_accepted(
        self, client: FlaskClient, instructor_fixture: dict[str, Any]
    ) -> None:
        """Genuine DOCX (with [Content_Types].xml & word/) must pass validation with HTTP 201."""
        inst = instructor_fixture["instructor"]
        course = instructor_fixture["course"]
        lesson = instructor_fixture["lesson"]
        csrf = login_instructor(client, inst.email)

        docx_buf = io.BytesIO()
        with zipfile.ZipFile(docx_buf, "w") as zf:
            zf.writestr("[Content_Types].xml", b'<?xml version="1.0" encoding="UTF-8"?><Types></Types>')
            zf.writestr("word/document.xml", b'<?xml version="1.0" encoding="UTF-8"?><w:document></w:document>')
        docx_bytes = docx_buf.getvalue()

        res_docx = client.post(
            f"/instructor/courses/{course.public_id}/lessons/{lesson.public_id}/resources",
            data={"file": (io.BytesIO(docx_bytes), "genuine.docx"), "label": "Giáo trình DOCX"},
            content_type="multipart/form-data",
            headers={"X-CSRF-Token": csrf},
        )
        assert res_docx.status_code == 201, f"Genuine DOCX rejected: {res_docx.get_json()}"

    def test_genuine_xlsx_accepted(
        self, client: FlaskClient, instructor_fixture: dict[str, Any]
    ) -> None:
        """Genuine XLSX (with [Content_Types].xml & xl/) must pass validation with HTTP 201."""
        inst = instructor_fixture["instructor"]
        course = instructor_fixture["course"]
        lesson = instructor_fixture["lesson"]
        csrf = login_instructor(client, inst.email)

        xlsx_buf = io.BytesIO()
        with zipfile.ZipFile(xlsx_buf, "w") as zf:
            zf.writestr("[Content_Types].xml", b'<?xml version="1.0" encoding="UTF-8"?><Types></Types>')
            zf.writestr("xl/workbook.xml", b'<?xml version="1.0" encoding="UTF-8"?><workbook></workbook>')
        xlsx_bytes = xlsx_buf.getvalue()

        res_xlsx = client.post(
            f"/instructor/courses/{course.public_id}/lessons/{lesson.public_id}/resources",
            data={"file": (io.BytesIO(xlsx_bytes), "genuine.xlsx"), "label": "Bảng tính XLSX"},
            content_type="multipart/form-data",
            headers={"X-CSRF-Token": csrf},
        )
        assert res_xlsx.status_code == 201, f"Genuine XLSX rejected: {res_xlsx.get_json()}"

    def test_genuine_pptx_accepted(
        self, client: FlaskClient, instructor_fixture: dict[str, Any]
    ) -> None:
        """Genuine PPTX (with [Content_Types].xml & ppt/) must pass validation with HTTP 201."""
        inst = instructor_fixture["instructor"]
        course = instructor_fixture["course"]
        lesson = instructor_fixture["lesson"]
        csrf = login_instructor(client, inst.email)

        pptx_buf = io.BytesIO()
        with zipfile.ZipFile(pptx_buf, "w") as zf:
            zf.writestr("[Content_Types].xml", b'<?xml version="1.0" encoding="UTF-8"?><Types></Types>')
            zf.writestr("ppt/presentation.xml", b'<?xml version="1.0" encoding="UTF-8"?><presentation></presentation>')
        pptx_bytes = pptx_buf.getvalue()

        res_pptx = client.post(
            f"/instructor/courses/{course.public_id}/lessons/{lesson.public_id}/resources",
            data={"file": (io.BytesIO(pptx_bytes), "genuine.pptx"), "label": "Bài giảng PPTX"},
            content_type="multipart/form-data",
            headers={"X-CSRF-Token": csrf},
        )
        assert res_pptx.status_code == 201, f"Genuine PPTX rejected: {res_pptx.get_json()}"


# ==============================================================================
# CHALLENGE 2: 50MB Ceiling & 50,000,001 Bytes Rejection
# ==============================================================================


class TestChallenge2FiftyMegabyteCeiling:
    """Verify strict 50,000,000 bytes ceiling: 50,000,001 bytes is rejected (HTTP 413 / validation error)."""

    def test_upload_50_000_001_bytes_rejected_via_api(
        self, client: FlaskClient, instructor_fixture: dict[str, Any]
    ) -> None:
        """Uploading 50,000,001 bytes via API returns HTTP 413 or 400 validation error."""
        inst = instructor_fixture["instructor"]
        course = instructor_fixture["course"]
        lesson = instructor_fixture["lesson"]
        csrf = login_instructor(client, inst.email)

        class LazyOversizedStream(io.BytesIO):
            """Stream exactly 50,000,001 bytes without allocating 50MB buffer in memory."""

            def __init__(self, size: int) -> None:
                super().__init__()
                self._size = size
                self._pos = 0

            def read(self, size: int = -1) -> bytes:
                if self._pos >= self._size:
                    return b""
                chunk_len = min(size if size > 0 else 65536, self._size - self._pos)
                self._pos += chunk_len
                return b"X" * chunk_len

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

        oversized = LazyOversizedStream(50_000_001)

        res = client.post(
            f"/instructor/courses/{course.public_id}/lessons/{lesson.public_id}/resources",
            data={"file": (oversized, "huge_document.pdf"), "label": "Tài liệu quá khổ"},
            content_type="multipart/form-data",
            headers={"X-CSRF-Token": csrf},
        )
        assert res.status_code in (413, 400), f"Expected 413 or 400, got {res.status_code}: {res.get_json()}"

    def test_check_file_size_limit_boundary_conditions(self, app: Flask) -> None:
        """Empirically test exact boundary: 50,000,000 is accepted, 50,000,001 is rejected."""
        # 50,000,000 bytes (exactly 50MB) must NOT raise
        check_file_size_limit(50_000_000, "large.pdf")
        check_file_size_limit(50_000_000, "large.docx")
        check_file_size_limit(50_000_000, "large.dwg")
        check_file_size_limit(50_000_000, "large.obj")

        # 50,000,001 bytes (50MB + 1 byte) MUST raise FileSizeLimitExceededError
        with pytest.raises(FileSizeLimitExceededError):
            check_file_size_limit(50_000_001, "boundary.pdf")

        with pytest.raises(FileSizeLimitExceededError):
            check_file_size_limit(50_000_001, "boundary.docx")

        with pytest.raises(FileSizeLimitExceededError):
            check_file_size_limit(50_000_001, "boundary.dwg")

        with pytest.raises(FileSizeLimitExceededError):
            check_file_size_limit(50_000_001, "boundary.obj")

    def test_store_file_stream_rejects_50_000_001_bytes(
        self, instructor_fixture: dict[str, Any]
    ) -> None:
        """store_file_stream raises FileSizeLimitExceededError when stream reaches 50,000,001 bytes."""
        inst = instructor_fixture["instructor"]
        course = instructor_fixture["course"]

        class CountingStream:
            def __init__(self, total_bytes: int) -> None:
                self.remaining = total_bytes

            def read(self, n: int = -1) -> bytes:
                if self.remaining <= 0:
                    return b""
                take = min(n if n > 0 else 65536, self.remaining)
                self.remaining -= take
                return b"B" * take

        oversized_stream = CountingStream(50_000_001)

        with pytest.raises(FileSizeLimitExceededError):
            store_file_stream(
                actor=inst,
                course_id=course.public_id,
                file_stream=oversized_stream,  # type: ignore[arg-type]
                filename="oversized_plan.dwg",
                session=db.session,
            )

    def test_limiting_stream_aborts_early_without_unbounded_buffering(self) -> None:
        """LimitingStream aborts early at 50,000,000 bytes without loading excess stream data."""
        class InfiniteStream:
            def read(self, size: int = -1) -> bytes:
                return b"A" * (size if size > 0 else 65536)

        limiter = LimitingStream(InfiniteStream(), max_bytes=50_000_000)
        with pytest.raises(FileSizeLimitExceededError):
            while True:
                chunk = limiter.read(1024 * 1024)
                if not chunk:
                    break


# ==============================================================================
# CHALLENGE 3: Staging State Draft & Resource Preservation on Text Update
# ==============================================================================


class TestChallenge3StagingDraftResourcePreservation:
    """Verify that uploading a resource in staging state creates a draft lesson,
    and subsequent text updates with identical title/content do NOT delete the draft lesson or its resource.
    """

    def test_staging_draft_preserved_on_identical_text_autosave(
        self, client: FlaskClient, instructor_fixture: dict[str, Any]
    ) -> None:
        """Canonical test:
        1. Course & Lesson are PUBLISHED.
        2. Upload resource -> creates staged draft lesson with the resource.
        3. Send PUT /instructor/lessons/<live_lesson_id> with identical text fields.
        4. Staged draft lesson must NOT be deleted (deleted_at is None), and resource must remain attached.
        """
        inst = instructor_fixture["instructor"]
        course = instructor_fixture["course"]
        lesson = instructor_fixture["lesson"]
        csrf = login_instructor(client, inst.email)

        # Capture initial state
        assert lesson.status == "PUBLISHED"
        assert lesson.deleted_at is None
        initial_resources_count = len(lesson.resources)

        # 1. Upload a resource to the published lesson (triggers staging)
        handout_pdf = b"%PDF-1.4\n1 0 obj\n<< >>\nendobj\ntrailer\n<< >>\n%%EOF"
        res_upload = client.post(
            f"/instructor/courses/{course.public_id}/lessons/{lesson.public_id}/resources",
            data={"file": (io.BytesIO(handout_pdf), "lecture_notes.pdf"), "label": "Ghi chú bài học"},
            content_type="multipart/form-data",
            headers={"X-CSRF-Token": csrf},
        )
        assert res_upload.status_code == 201, f"Resource upload failed: {res_upload.get_json()}"
        upload_data = res_upload.get_json()
        staged_lesson_public_id = upload_data.get("lesson_id")
        assert staged_lesson_public_id is not None
        assert staged_lesson_public_id != str(lesson.public_id), "Staging should return a distinct draft lesson public ID"

        # Locate staged draft lesson in database
        staged_lesson = (
            db.session.query(Lesson)
            .filter(Lesson.public_id == uuid.UUID(staged_lesson_public_id))
            .first()
        )
        assert staged_lesson is not None, "Staged draft lesson was not found in DB"
        assert staged_lesson.status == "DRAFT"
        assert staged_lesson.deleted_at is None
        assert len(staged_lesson.resources) == initial_resources_count + 1

        # 2. Immediately send text update with identical title and content targeting the published lesson
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
        assert res_autosave.status_code == 200, f"Text autosave failed: {res_autosave.get_json()}"
        autosave_data = res_autosave.get_json()

        # Refresh database session state
        db.session.refresh(staged_lesson)
        db.session.refresh(lesson)

        # 3. EMPIRICAL VERIFICATIONS
        # The staged draft MUST NOT be soft-deleted because has_resource_diff is True!
        assert staged_lesson.deleted_at is None, (
            "CRITICAL BUG: Staged draft lesson was erroneously soft-deleted by identical text autosave!"
        )
        assert len(staged_lesson.resources) == initial_resources_count + 1, (
            "CRITICAL BUG: Attached resource was lost or detached from staged draft lesson!"
        )
        assert autosave_data.get("is_draft") is True, (
            "Autosave response should acknowledge active draft state when resources differ"
        )

        # Live lesson must remain untouched and published
        assert lesson.status == "PUBLISHED"
        assert lesson.deleted_at is None
        assert len(lesson.resources) == initial_resources_count

    def test_staging_draft_preserved_under_multiple_consecutive_identical_autosaves(
        self, client: FlaskClient, instructor_fixture: dict[str, Any]
    ) -> None:
        """Autosave triggers repeatedly in real clients (e.g. debounced 800ms).
        Verify that 5 consecutive identical text updates NEVER delete the draft or drop resources.
        """
        inst = instructor_fixture["instructor"]
        course = instructor_fixture["course"]
        lesson = instructor_fixture["lesson"]
        csrf = login_instructor(client, inst.email)

        # Upload resource
        res_upload = client.post(
            f"/instructor/courses/{course.public_id}/lessons/{lesson.public_id}/resources",
            data={"file": (io.BytesIO(b"%PDF-1.4\nRepetitive Autosave Handout\n%%EOF"), "handout_repeat.pdf"), "label": "Handout"},
            content_type="multipart/form-data",
            headers={"X-CSRF-Token": csrf},
        )
        assert res_upload.status_code == 201
        staged_id = res_upload.get_json().get("lesson_id")
        staged_lesson = db.session.query(Lesson).filter(Lesson.public_id == uuid.UUID(staged_id)).first()
        assert staged_lesson is not None

        # Execute 5 consecutive identical autosaves
        for i in range(5):
            res = client.put(
                f"/instructor/lessons/{lesson.public_id}",
                json={
                    "title": lesson.title,
                    "markdown_content": lesson.markdown_content,
                    "summary": lesson.summary,
                    "estimated_duration_minutes": lesson.estimated_duration_minutes,
                },
                headers={"X-CSRF-Token": csrf},
            )
            assert res.status_code == 200, f"Autosave iteration {i} failed: {res.get_json()}"
            db.session.refresh(staged_lesson)
            assert staged_lesson.deleted_at is None, f"Draft soft-deleted on iteration {i}!"
            assert len(staged_lesson.resources) >= 1, f"Resource lost on iteration {i}!"

    def test_draft_deletion_allowed_only_when_no_resource_diff_and_identical_text(
        self, client: FlaskClient, instructor_fixture: dict[str, Any]
    ) -> None:
        """Contrast experiment: when there is NO resource difference and text is reverted to match live,
        the draft lesson is legitimately cleaned up (deleted_at set) to avoid orphaned empty drafts.
        """
        inst = instructor_fixture["instructor"]
        course = instructor_fixture["course"]
        lesson = instructor_fixture["lesson"]
        csrf = login_instructor(client, inst.email)

        # 1. Modify text to create a draft with NO new resources
        res_edit = client.put(
            f"/instructor/lessons/{lesson.public_id}",
            json={
                "title": "Tên Mới Bản Nháp",
                "markdown_content": lesson.markdown_content,
                "summary": lesson.summary,
                "estimated_duration_minutes": lesson.estimated_duration_minutes,
            },
            headers={"X-CSRF-Token": csrf},
        )
        assert res_edit.status_code == 200
        draft_id = res_edit.get_json().get("lesson_id")
        assert draft_id is not None
        draft_lesson = db.session.query(Lesson).filter(Lesson.public_id == uuid.UUID(draft_id)).first()
        assert draft_lesson is not None
        assert draft_lesson.status == "DRAFT"
        assert draft_lesson.deleted_at is None

        # 2. Revert text to match live lesson exactly (no resource diff exists)
        res_revert = client.put(
            f"/instructor/lessons/{lesson.public_id}",
            json={
                "title": lesson.title,
                "markdown_content": lesson.markdown_content,
                "summary": lesson.summary,
                "estimated_duration_minutes": lesson.estimated_duration_minutes,
            },
            headers={"X-CSRF-Token": csrf},
        )
        assert res_revert.status_code == 200
        assert res_revert.get_json().get("is_draft") is False

        # Now the draft should be deleted because it is truly identical with zero resource difference
        db.session.refresh(draft_lesson)
        assert draft_lesson.deleted_at is not None, "Draft without resource diff should be cleaned up on revert"
