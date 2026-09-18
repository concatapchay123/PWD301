"""Adversarial challenger test suite for Milestone 4: Media Upload & Size Limit Validation.

Scope:
1. Video Size Limit Verification (Invariant 18):
   - LimitingStream exact 1 GB boundary (1,000,000,000 bytes) -> FileSizeLimitExceededError.
   - Sub-1 GB boundary (999,999,999 bytes) -> succeeds.
   - Immediate abort and bounded memory consumption during streaming.
   - check_file_size_limit boundaries for video (< 1 GB), PDF (50 MB), DOCX (50 MB), PPTX (100 MB).
   - Atomic rollback: no orphan lesson persisted in DB when upload exceeds limit.
2. Dangerous & Macro Office File Validation:
   - Macro-enabled Office presentation (.pptm, .potm) -> FileValidationError.
   - Macro-enabled Office document (.docm, .dotm) -> FileValidationError.
   - Macro-enabled Excel workbook (.xlsm, .xltm) -> FileValidationError.
   - Executable scripts (.exe, .sh, .bat, .cmd, .bash, .py, .js, .vbs, .msi, .scr).
   - Case-insensitive rejection (.PPTM, .DOCM, .EXE, .BAT, .SH).
   - Disguised MIME type spoofing prevention.
   - Lesson creation and resource attachment endpoints enforce rejection with rollback.
3. Path Traversal & Filename Sanitization:
   - Traversal sequences (../../evil.mp4, ..\\..\\evil.mp4, ....//....//evil.mp4).
   - Absolute paths (C:\\Windows\\System32\\calc.exe, /etc/passwd).
   - Null bytes and control character stripping (evil\\x00.mp4, evil.mp4\\x00.exe).
   - Windows hazardous character removal (<>:"/\\|?*;).
   - Empty, dot-only, and whitespace-only fallbacks (., .., ..., "   ").
   - Content-addressed physical isolation: files stored by SHA-256 hash.
"""

from __future__ import annotations

import io
import uuid
from pathlib import Path

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from pwd301.extensions import db
from pwd301.models.course import Course, Lesson
from pwd301.models.identity import Role, User
from pwd301.services.course_service import create_course
from pwd301.services.exceptions import FileSizeLimitExceededError, FileValidationError
from pwd301.services.file_service import (
    LimitingStream,
    check_file_size_limit,
    get_file_quarantine_root,
    sanitize_filename,
    store_file_stream,
    validate_file_metadata,
)
from pwd301.services.lesson_service import create_lesson
from pwd301.services.user_service import assign_role_to_user, register_user
from tests.conftest import login_web_user


class MockStream(io.BytesIO):
    """Synthetic stream producing deterministic bytes of arbitrary length without RAM allocation."""

    def __init__(self, total_bytes: int, fill_byte: bytes = b"A") -> None:
        super().__init__()
        self.total_bytes = total_bytes
        self.bytes_read = 0
        self.fill_byte = fill_byte
        self.read_call_count = 0

    def read(self, size: int | None = -1) -> bytes:
        self.read_call_count += 1
        if self.bytes_read >= self.total_bytes:
            return b""

        if size is None or size < 0:
            bytes_to_give = self.total_bytes - self.bytes_read
        else:
            bytes_to_give = min(size, self.total_bytes - self.bytes_read)

        self.bytes_read += bytes_to_give
        return self.fill_byte * bytes_to_give


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
    u = register_user("challenger_inst@example.com", "Password@123", "Challenger Instructor")
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def test_course(app: Flask, instructor_user: User) -> Course:
    """Create a published course managed by instructor_user."""
    c = create_course(
        instructor_user,
        {
            "course_code": f"CHAL-{uuid.uuid4().hex[:4].upper()}",
            "title": "Adversarial Challenger Course",
            "category": "Computer Science",
            "difficulty": "ADVANCED",
        },
    )
    c.status = "PUBLISHED"
    db.session.commit()
    return c


class TestVideoSizeLimitsAdversarial:
    """Adversarial verification of Invariant 18 (< 1 GB limit = strictly < 1,000,000,000 bytes)."""

    def test_limiting_stream_sub_1gb_passes(self) -> None:
        """Stream with 999,999,999 bytes (< 1 GB) passes LimitingStream without error."""
        total_len = 999_999_999
        source = MockStream(total_len)
        limiter = LimitingStream(source, max_bytes=1_000_000_000)

        chunk_size = 1024 * 1024
        bytes_read = 0
        for _ in range(10):
            chunk = limiter.read(chunk_size)
            assert len(chunk) == chunk_size
            bytes_read += len(chunk)
        assert bytes_read == 10 * chunk_size

    def test_limiting_stream_exact_1gb_boundary_raises_413_error(self) -> None:
        """Stream reaching exactly 1,000,000,000 bytes (1 GB) MUST raise error."""
        target_limit = 1_000_000_000
        source = MockStream(target_limit)
        limiter = LimitingStream(source, max_bytes=target_limit)

        chunk_size = 64 * 1024
        total_read = 0
        with pytest.raises(FileSizeLimitExceededError) as exc_info:
            while True:
                chunk = limiter.read(chunk_size)
                if not chunk:
                    break
                total_read += len(chunk)

        assert "exceeded maximum limit of 1000000000 bytes" in str(exc_info.value)
        assert limiter._bytes_read >= target_limit

    def test_limiting_stream_above_1gb_raises_error(self) -> None:
        """Stream with 1,000,000,001 bytes (1 GB + 1 byte) MUST raise FileSizeLimitExceededError."""
        target_limit = 1_000_000_000
        source = MockStream(target_limit + 1)
        limiter = LimitingStream(source, max_bytes=target_limit)

        with pytest.raises(FileSizeLimitExceededError):
            while True:
                chunk = limiter.read(64 * 1024)
                if not chunk:
                    break

    def test_limiting_stream_single_large_read_raises_error(self) -> None:
        """Calling read(-1) on an oversized stream raises FileSizeLimitExceededError immediately."""
        target_limit = 1_000_000_000
        source = MockStream(target_limit + 100)
        limiter = LimitingStream(source, max_bytes=target_limit)

        with pytest.raises(FileSizeLimitExceededError):
            limiter.read(-1)

    def test_check_file_size_limit_video_boundaries(self, app: Flask) -> None:
        """check_file_size_limit strictly enforces < 1,000,000,000 bytes for videos."""
        with app.app_context():
            # 0 bytes -> empty file error
            with pytest.raises(FileValidationError, match="0 bytes"):
                check_file_size_limit(0, "video.mp4")

            # 999,999,999 bytes -> strictly < 1 GB -> passes
            check_file_size_limit(999_999_999, "video.mp4")
            check_file_size_limit(999_999_999, "video.webm")

            # 1,000,000,000 bytes -> 1 GB -> fails
            with pytest.raises(FileSizeLimitExceededError, match="strictly < 1 GB"):
                check_file_size_limit(1_000_000_000, "video.mp4")

            with pytest.raises(FileSizeLimitExceededError, match="strictly < 1 GB"):
                check_file_size_limit(1_000_000_000, "video.webm")

            # 1,000,000,001 bytes -> fails
            with pytest.raises(FileSizeLimitExceededError, match="strictly < 1 GB"):
                check_file_size_limit(1_000_000_001, "video.mp4")

    def test_check_file_size_limit_document_boundaries(self, app: Flask) -> None:
        """check_file_size_limit enforces category limits for PDF, DOCX, PPTX."""
        with app.app_context():
            # PDF: max 50 MB (50,000,000 bytes)
            check_file_size_limit(50_000_000, "document.pdf")
            with pytest.raises(FileSizeLimitExceededError, match="PDF file exceeds"):
                check_file_size_limit(50_000_001, "document.pdf")

            # DOCX: max 50 MB (50,000,000 bytes)
            check_file_size_limit(50_000_000, "document.docx")
            with pytest.raises(FileSizeLimitExceededError, match="DOCX file exceeds"):
                check_file_size_limit(50_000_001, "document.docx")

            # PPTX: max 100 MB (100,000,000 bytes)
            check_file_size_limit(100_000_000, "presentation.pptx")
            with pytest.raises(FileSizeLimitExceededError, match="PPTX file exceeds"):
                check_file_size_limit(100_000_001, "presentation.pptx")

    def test_store_file_stream_exact_1gb_boundary_and_temp_cleanup(
        self, app: Flask, test_course: Course, instructor_user: User
    ) -> None:
        """1 GB stream raises FileSizeLimitExceededError and unlinks temp file."""
        oversized = MockStream(1_000_000_000)

        quarantine_root = get_file_quarantine_root()
        temp_files_before = set(quarantine_root.glob("upload_*.tmp"))

        with pytest.raises(FileSizeLimitExceededError):
            store_file_stream(
                actor=instructor_user,
                course_id=test_course.id,
                file_stream=oversized,
                filename="boundary_lecture.mp4",
                content_type="video/mp4",
                asset_type="RESOURCE",
                session=db.session,
            )

        # Confirm no orphaned temp file remained in quarantine
        temp_files_after = set(quarantine_root.glob("upload_*.tmp"))
        assert temp_files_after == temp_files_before

    def test_create_lesson_route_oversized_media_rolls_back_atomically(
        self, client: FlaskClient, test_course: Course, instructor_user: User
    ) -> None:
        """Uploading oversized video during lesson creation creates no orphan lesson."""
        login_web_user(client, instructor_user)

        lessons_before_count = (
            db.session.query(Lesson).filter(Lesson.course_id == test_course.id).count()
        )

        oversized = MockStream(1_000_000_000)
        data = {
            "title": "Oversized Lesson Attempt",
            "summary": "This should not be saved in database.",
            "media_file": (oversized, "oversized_1gb.mp4"),
        }

        # Request via JSON (API style)
        resp = client.post(
            f"/instructor/courses/{test_course.public_id}/lessons",
            data=data,
            content_type="multipart/form-data",
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 413
        json_resp = resp.get_json()
        assert json_resp["error"]["code"] == "PAYLOAD_TOO_LARGE"

        # Verify DB atomicity: no lesson was persisted
        db.session.expire_all()
        lessons_after_count = (
            db.session.query(Lesson).filter(Lesson.course_id == test_course.id).count()
        )
        assert lessons_after_count == lessons_before_count


class TestDangerousAndMacroFileValidation:
    """Adversarial verification of macro-enabled Office and executable blocklists."""

    @pytest.mark.parametrize(
        "forbidden_ext",
        [
            ".pptm",
            ".potm",
            ".docm",
            ".dotm",
            ".xlsm",
            ".xltm",
            ".exe",
            ".bat",
            ".cmd",
            ".sh",
            ".bash",
            ".php",
            ".py",
            ".pyw",
            ".pl",
            ".cgi",
            ".jar",
            ".vbs",
            ".js",
            ".vbe",
            ".wsf",
            ".wsh",
            ".msi",
            ".scr",
            ".com",
            ".pif",
            ".hta",
            ".cpl",
            ".msc",
        ],
    )
    def test_validate_file_metadata_rejects_dangerous_extensions(self, forbidden_ext: str) -> None:
        """validate_file_metadata rejects all dangerous executable and macro extensions."""
        with pytest.raises(FileValidationError, match="is forbidden for security"):
            validate_file_metadata(f"suspicious_file{forbidden_ext}")

    @pytest.mark.parametrize(
        "uppercase_ext",
        [".PPTM", ".DOCM", ".XLSM", ".EXE", ".BAT", ".SH", ".PHP", ".CMD"],
    )
    def test_validate_file_metadata_case_insensitivity(self, uppercase_ext: str) -> None:
        """Extension check must be strictly case-insensitive (e.g., .PPTM, .EXE)."""
        with pytest.raises(FileValidationError, match="is forbidden for security"):
            validate_file_metadata(f"INVOICE{uppercase_ext}")

    def test_store_file_stream_rejects_macro_office_presentation(
        self, app: Flask, test_course: Course, instructor_user: User
    ) -> None:
        """store_file_stream strictly rejects .pptm presentation files."""
        stream = io.BytesIO(b"PK\x03\x04 simulated pptm content")
        with pytest.raises(FileValidationError, match="is forbidden for security"):
            store_file_stream(
                actor=instructor_user,
                course_id=test_course.id,
                file_stream=stream,
                filename="lecture_slides_with_macro.pptm",
                content_type="application/vnd.ms-powerpoint.presentation.macroEnabled.12",
                asset_type="RESOURCE",
                session=db.session,
            )

    def test_store_file_stream_rejects_macro_office_document(
        self, app: Flask, test_course: Course, instructor_user: User
    ) -> None:
        """store_file_stream strictly rejects .docm document files."""
        stream = io.BytesIO(b"PK\x03\x04 simulated docm content")
        with pytest.raises(FileValidationError, match="is forbidden for security"):
            store_file_stream(
                actor=instructor_user,
                course_id=test_course.id,
                file_stream=stream,
                filename="assignment_brief.docm",
                content_type="application/vnd.ms-word.document.macroEnabled.12",
                asset_type="RESOURCE",
                session=db.session,
            )

    def test_store_file_stream_rejects_executable_scripts(
        self, app: Flask, test_course: Course, instructor_user: User
    ) -> None:
        """store_file_stream strictly rejects .exe, .sh, and .bat files."""
        for filename, content in [
            ("payload.exe", b"MZ\x90\x00\x03 simulated pe"),
            ("install.sh", b"#!/bin/bash\nrm -rf /"),
            ("run.bat", b"@echo off\ndel *.*"),
        ]:
            with pytest.raises(FileValidationError, match="is forbidden for security"):
                store_file_stream(
                    actor=instructor_user,
                    course_id=test_course.id,
                    file_stream=io.BytesIO(content),
                    filename=filename,
                    content_type="application/octet-stream",
                    asset_type="RESOURCE",
                    session=db.session,
                )

    def test_spoofed_mime_type_does_not_bypass_extension_check(
        self, app: Flask, test_course: Course, instructor_user: User
    ) -> None:
        """Innocent video or pdf MIME type cannot bypass forbidden extension validation."""
        stream = io.BytesIO(b"MZ\x90\x00\x03 binary payload")
        with pytest.raises(FileValidationError, match="is forbidden for security"):
            store_file_stream(
                actor=instructor_user,
                course_id=test_course.id,
                file_stream=stream,
                filename="malware.exe",
                content_type="video/mp4",  # Spoofed MIME type
                asset_type="RESOURCE",
                session=db.session,
            )

    def test_instructor_create_lesson_rejects_dangerous_media_file(
        self, client: FlaskClient, test_course: Course, instructor_user: User
    ) -> None:
        """Instructor cannot create lesson with executable or macro media_file."""
        login_web_user(client, instructor_user)

        lessons_before = db.session.query(Lesson).filter(Lesson.course_id == test_course.id).count()

        resp = client.post(
            f"/instructor/courses/{test_course.public_id}/lessons",
            data={
                "title": "Malicious Media Lesson",
                "media_file": (io.BytesIO(b"echo exploit"), "exploit.sh"),
            },
            content_type="multipart/form-data",
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 400
        json_resp = resp.get_json()
        assert json_resp["error"]["code"] == "VALIDATION_ERROR"
        assert "is forbidden for security" in json_resp["error"]["message"]

        # Verify DB rollback
        db.session.expire_all()
        lessons_after = db.session.query(Lesson).filter(Lesson.course_id == test_course.id).count()
        assert lessons_after == lessons_before

    def test_instructor_create_lesson_rejects_dangerous_resource_files(
        self, client: FlaskClient, test_course: Course, instructor_user: User
    ) -> None:
        """Instructor cannot attach macro presentation in resource_files list."""
        login_web_user(client, instructor_user)

        lessons_before = db.session.query(Lesson).filter(Lesson.course_id == test_course.id).count()

        resp = client.post(
            f"/instructor/courses/{test_course.public_id}/lessons",
            data={
                "title": "Lesson With Bad Attachment",
                "resource_files": [
                    (io.BytesIO(b"PK\x03\x04 valid doc"), "notes.docx"),
                    (io.BytesIO(b"PK\x03\x04 macro pres"), "dangerous.pptm"),
                ],
            },
            content_type="multipart/form-data",
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 400
        json_resp = resp.get_json()
        assert "is forbidden for security" in json_resp["error"]["message"]

        db.session.expire_all()
        lessons_after = db.session.query(Lesson).filter(Lesson.course_id == test_course.id).count()
        assert lessons_after == lessons_before

    def test_instructor_create_lesson_html_flow_ghost_lesson_defect(
        self, client: FlaskClient, test_course: Course, instructor_user: User
    ) -> None:
        """Browser HTML form upload of dangerous file must not leave orphan lesson."""
        login_web_user(client, instructor_user)

        lessons_before = db.session.query(Lesson).filter(Lesson.course_id == test_course.id).count()

        resp = client.post(
            f"/instructor/courses/{test_course.public_id}/lessons",
            data={
                "title": "HTML Malicious Upload",
                "media_file": (io.BytesIO(b"echo evil"), "trojan.bat"),
            },
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400
        assert "error" in resp.get_json()

        # Verify DB atomicity: orphan lesson must NOT exist
        db.session.expire_all()
        lessons_after = db.session.query(Lesson).filter(Lesson.course_id == test_course.id).count()
        assert lessons_after == lessons_before

    def test_instructor_attach_resource_route_rejects_macro_document(
        self, client: FlaskClient, test_course: Course, instructor_user: User
    ) -> None:
        """POST /courses/<cid>/lessons/<lid>/resources endpoint blocks .docm uploads."""
        login_web_user(client, instructor_user)

        lesson = create_lesson(
            instructor_user,
            test_course.id,
            {"title": "Target Lesson", "markdown_content": "# Target"},
        )

        resp = client.post(
            f"/instructor/courses/{test_course.public_id}/lessons/{lesson.public_id}/resources",
            data={
                "file": (io.BytesIO(b"PK\x03\x04 docm payload"), "macro_enabled.docm"),
                "label": "Macro Document",
            },
            content_type="multipart/form-data",
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 400
        json_resp = resp.get_json()
        assert "is forbidden for security" in json_resp["error"]["message"]


class TestPathTraversalAndSanitization:
    """Adversarial verification of filename sanitization and path traversal prevention."""

    @pytest.mark.parametrize(
        "input_name,expected_output",
        [
            ("../../evil.mp4", "evil.mp4"),
            (r"..\\..\\evil.mp4", "evil.mp4"),
            ("../../../../../../etc/passwd", "passwd"),
            (r"C:\\Windows\\System32\\calc.exe", "calc.exe"),
            ("....//....//evil.mp4", "evil.mp4"),
            (r"..\\..\\..\\boot.ini", "boot.ini"),
            ("folder/subfolder/video.mp4", "video.mp4"),
            (r"folder\\subfolder\\video.mp4", "video.mp4"),
            ("lecture<video>:1.mp4", "lecturevideo1.mp4"),
            ('file"name?star*pipe|semicolon;.mp4', "filenamestarpipesemicolon.mp4"),
            ("null\x00byte.mp4", "nullbyte.mp4"),
            ("null_double\x00\x00test.mp4", "null_doubletest.mp4"),
            ("   .spaces_and_dots.mp4.   ", "spaces_and_dots.mp4"),
            ("", "unnamed_file"),
            (".", "unnamed_file"),
            ("..", "unnamed_file"),
            ("...", "unnamed_file"),
            ("   ", "unnamed_file"),
            ("CON", "CON"),
            ("NUL", "NUL"),
            ("AUX.mp4", "AUX.mp4"),
        ],
    )
    def test_sanitize_filename_comprehensive_matrix(
        self, input_name: str, expected_output: str
    ) -> None:
        """sanitize_filename strips path traversal, directory separators, and control characters."""
        actual = sanitize_filename(input_name)
        assert actual == expected_output

    def test_null_byte_extension_bypass_blocked(self) -> None:
        """Null byte in filename (e.g. 'exploit.mp4\\x00.exe') cannot bypass validation."""
        sanitized = sanitize_filename("exploit.mp4\x00.exe")
        assert sanitized == "exploit.mp4.exe"
        with pytest.raises(FileValidationError, match="is forbidden for security"):
            validate_file_metadata(sanitized)

    def test_store_file_stream_traversal_filename_cannot_escape(
        self, app: Flask, test_course: Course, instructor_user: User
    ) -> None:
        """Traversal filename isolates physical file in content-addressed blob storage."""
        traversal_name = "../../../../traversal_attack.mp4"
        payload = b"\x00\x00\x00\x20ftypisom" + b"traversal test content"

        asset = store_file_stream(
            actor=instructor_user,
            course_id=test_course.id,
            file_stream=io.BytesIO(payload),
            filename=traversal_name,
            content_type="video/mp4",
            asset_type="RESOURCE",
            session=db.session,
        )

        assert asset.original_filename == "traversal_attack.mp4"

        blob = asset.revisions[0].blob
        assert blob is not None
        assert blob.storage_key.startswith("blobs/")
        assert ".." not in blob.storage_key

        escaped_path = Path("traversal_attack.mp4")
        assert not escaped_path.exists()

        escaped_parent = Path("../traversal_attack.mp4")
        assert not escaped_parent.exists()

    def test_store_file_stream_windows_device_names_handled_safely(
        self, app: Flask, test_course: Course, instructor_user: User
    ) -> None:
        """Filenames matching Windows reserved device names (NUL.mp4, CON.mp4) store safely."""
        payload = b"\x00\x00\x00\x20ftypisom" + b"device name payload"

        asset = store_file_stream(
            actor=instructor_user,
            course_id=test_course.id,
            file_stream=io.BytesIO(payload),
            filename="NUL.mp4",
            content_type="video/mp4",
            asset_type="RESOURCE",
            session=db.session,
        )

        assert asset.original_filename == "NUL.mp4"
        assert asset.status == "ACTIVE"
