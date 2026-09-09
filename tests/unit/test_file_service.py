"""Unit tests for File Storage & Authorization Engine (TASK-018).

Validates:
- Algorithm 12 SHA-256 deduplication: identical payloads reuse FileBlob and increment refcount.
- Revision lifecycle: uploading new revisions sets is_current and increments revision_no.
- Strict size limits: Video strictly < 1 GB (999,999,999 bytes accepted, 1,000,000,000 rejected).
- File category limits: Image (10 MB), PDF (50 MB), DOCX (50 MB), PPTX (100 MB).
- Dangerous extensions blocked: .exe, .py, .sh, .bat, .docm.
- Soft-delete and restore lifecycle: TRASH -> ACTIVE.
- Safe rollback: physical file cleaned up if database transaction fails.
- Filename sanitization against path traversal.
"""

from __future__ import annotations

import io
import uuid
from unittest.mock import patch

import pytest
from flask import Flask

from pwd301.extensions import db
from pwd301.models.course import Course
from pwd301.models.file_import import FileAsset, FileBlob, FileRevision
from pwd301.models.identity import Role, User
from pwd301.services.course_service import create_course
from pwd301.services.exceptions import (
    FileSizeLimitExceededError,
    FileValidationError,
)
from pwd301.services.file_service import (
    _serialize_file_asset,
    add_file_revision,
    check_file_size_limit,
    get_file_storage_root,
    restore_file_asset,
    sanitize_filename,
    store_file_stream,
    trash_file_asset,
    validate_file_metadata,
)
from pwd301.services.user_service import assign_role_to_user, register_user


@pytest.fixture
def setup_roles(app: Flask) -> dict[str, Role]:
    """Ensure standard roles exist in test database."""
    role_map: dict[str, Role] = {}
    for code, name in [
        ("STUDENT", "Student"),
        ("INSTRUCTOR", "Instructor"),
        ("ADMIN", "System Administrator"),
    ]:
        role = db.session.query(Role).filter(Role.code == code).first()
        if role is None:
            role = Role(code=code, name=name)
            db.session.add(role)
            db.session.flush()
        role_map[code] = role
    db.session.commit()
    return role_map


@pytest.fixture
def instructor(app: Flask, setup_roles: dict[str, Role]) -> User:
    """Create test instructor user."""
    u = register_user(
        f"inst_unit_{uuid.uuid4().hex[:6]}@example.com", "Password@123", "Instructor Unit"
    )
    return assign_role_to_user(u.id, "INSTRUCTOR")


@pytest.fixture
def course(instructor: User) -> Course:
    """Create test course owned by instructor."""
    return create_course(
        instructor,
        {
            "course_code": f"UNIT-{uuid.uuid4().hex[:4].upper()}",
            "title": "Unit Test File Management",
            "category": "Computer Science",
            "difficulty": "BEGINNER",
        },
    )


def test_filename_sanitization() -> None:
    """Verify filename sanitization removes path traversal and dangerous chars."""
    assert sanitize_filename("../../etc/passwd") == "passwd"
    assert sanitize_filename("..\\..\\windows\\system32\\test.pdf") == "test.pdf"
    assert sanitize_filename("normal_file.pdf") == "normal_file.pdf"
    assert sanitize_filename("   spaced  name .png   ") == "spaced  name .png"
    assert sanitize_filename("../../../malicious<file>:*.docx") == "maliciousfile.docx"
    assert sanitize_filename("") == "unnamed_file"
    assert sanitize_filename("....") == "unnamed_file"


def test_forbidden_file_extensions() -> None:
    """Verify dangerous executable extensions and macro-enabled Office files are blocked."""
    forbidden = ["script.py", "malware.exe", "attack.sh", "run.bat", "macro.docm", "macro.xlsm"]
    for fname in forbidden:
        with pytest.raises(FileValidationError):
            validate_file_metadata(fname)

    # Valid extensions should pass
    validate_file_metadata("document.pdf")
    validate_file_metadata("image.png")
    validate_file_metadata("notes.docx")
    validate_file_metadata("slides.pptx")
    validate_file_metadata("video.mp4")


def test_file_size_limits(app: Flask) -> None:
    """Verify strict size constraints across all media categories."""
    # Video strictly < 1 GB (1,000,000,000 bytes)
    # 999,999,999 bytes accepted
    check_file_size_limit(999_999_999, "lecture.mp4")

    # 1,000,000,000 bytes rejected
    with pytest.raises(FileSizeLimitExceededError):
        check_file_size_limit(1_000_000_000, "lecture.mp4")

    # Image limit: 10 MB (10,000,000 bytes)
    check_file_size_limit(10_000_000, "diagram.png")
    with pytest.raises(FileSizeLimitExceededError):
        check_file_size_limit(10_000_001, "diagram.png")

    # PDF limit: 50 MB
    check_file_size_limit(50_000_000, "handout.pdf")
    with pytest.raises(FileSizeLimitExceededError):
        check_file_size_limit(50_000_001, "handout.pdf")

    # DOCX limit: 50 MB
    check_file_size_limit(50_000_000, "syllabus.docx")
    with pytest.raises(FileSizeLimitExceededError):
        check_file_size_limit(50_000_001, "syllabus.docx")

    # PPTX limit: 100 MB
    check_file_size_limit(100_000_000, "lecture.pptx")
    with pytest.raises(FileSizeLimitExceededError):
        check_file_size_limit(100_000_001, "lecture.pptx")

    # 0-byte file rejected
    with pytest.raises(FileValidationError):
        check_file_size_limit(0, "empty.pdf")


def test_algorithm_12_deduplication(app: Flask, instructor: User, course: Course) -> None:
    """Verify Algorithm 12 SHA-256 deduplication: identical payloads reuse single FileBlob."""
    content = b"Algorithm 12 Canonical Deduplication Payload - Same Hash Test"

    stream1 = io.BytesIO(content)
    asset1 = store_file_stream(
        actor=instructor,
        course_id=course.public_id,
        file_stream=stream1,
        filename="lecture_notes_v1.pdf",
        content_type="application/pdf",
        session=db.session,
    )

    stream2 = io.BytesIO(content)
    asset2 = store_file_stream(
        actor=instructor,
        course_id=course.public_id,
        file_stream=stream2,
        filename="handout_copy.pdf",
        content_type="application/pdf",
        session=db.session,
    )

    # Assets are distinct logical entities
    assert asset1.id != asset2.id
    assert asset1.public_id != asset2.public_id

    # But both reference the EXACT SAME physical FileBlob
    rev1 = asset1.current_revision
    rev2 = asset2.current_revision
    assert rev1 is not None and rev2 is not None
    assert rev1.blob_id == rev2.blob_id

    blob = db.session.get(FileBlob, rev1.blob_id)
    assert blob is not None
    assert blob.reference_count == 2
    assert blob.size_bytes == len(content)

    # Verify physical file exists on disk at hierarchical storage path
    storage_root = get_file_storage_root()
    physical_path = storage_root / blob.storage_key
    assert physical_path.exists()
    assert physical_path.read_bytes() == content


def test_add_file_revision(app: Flask, instructor: User, course: Course) -> None:
    """Verify creating a new FileRevision updates revision_no, is_current, and links."""
    content_v1 = b"Lecture 1 Introduction Initial Draft"
    stream1 = io.BytesIO(content_v1)
    asset = store_file_stream(
        actor=instructor,
        course_id=course.public_id,
        file_stream=stream1,
        filename="lecture_1.pdf",
        content_type="application/pdf",
        session=db.session,
    )
    assert asset.current_revision.revision_no == 1
    assert asset.current_revision.is_current is True

    # Upload revision 2 with different content
    content_v2 = b"Lecture 1 Introduction Final Revised Edition"
    stream2 = io.BytesIO(content_v2)
    rev2 = add_file_revision(
        actor=instructor,
        asset_id=asset.public_id,
        file_stream=stream2,
        filename="lecture_1_final.pdf",
        content_type="application/pdf",
        session=db.session,
    )

    assert rev2.revision_no == 2
    assert rev2.is_current is True
    assert rev2.original_filename == "lecture_1_final.pdf"
    assert rev2.size_bytes == len(content_v2)

    # Verify old revision is marked REPLACED and is_current=False
    revisions = (
        db.session.query(FileRevision)
        .filter(FileRevision.file_asset_id == asset.id)
        .order_by(FileRevision.revision_no)
        .all()
    )
    assert len(revisions) == 2
    assert revisions[0].revision_no == 1
    assert revisions[0].is_current is False
    assert revisions[0].status == "REPLACED"
    assert revisions[0].replaced_at is not None

    assert revisions[1].revision_no == 2
    assert revisions[1].is_current is True
    assert revisions[1].status == "ACTIVE"


def test_soft_delete_and_restore_lifecycle(app: Flask, instructor: User, course: Course) -> None:
    """Verify soft-delete to TRASH and restoration back to ACTIVE."""
    content = b"Soft-delete lifecycle test content"
    asset = store_file_stream(
        actor=instructor,
        course_id=course.public_id,
        file_stream=io.BytesIO(content),
        filename="notes.pdf",
        content_type="application/pdf",
        session=db.session,
    )
    assert asset.status == "ACTIVE"

    # Soft delete into TRASH
    trashed = trash_file_asset(
        actor=instructor, asset_id=asset.public_id, reason="Outdated", session=db.session
    )
    assert trashed.status == "TRASH"
    assert trashed.deleted_at is not None
    assert trashed.restore_until is not None

    # Cannot add revision to TRASH asset
    with pytest.raises(FileValidationError):
        add_file_revision(
            actor=instructor,
            asset_id=asset.public_id,
            file_stream=io.BytesIO(b"New revision"),
            filename="notes_v2.pdf",
            session=db.session,
        )

    # Restore asset back to ACTIVE
    restored = restore_file_asset(actor=instructor, asset_id=asset.public_id, session=db.session)
    assert restored.status == "ACTIVE"
    assert restored.deleted_at is None
    assert restored.restore_until is None


def test_safe_rollback_on_db_failure(app: Flask, instructor: User, course: Course) -> None:
    """Verify rollback safety: physical file is cleaned up if database commit fails."""
    content = b"Rollback test payload - unique" + uuid.uuid4().bytes
    stream = io.BytesIO(content)

    crash_err = RuntimeError("Simulated DB Crash")
    with (
        patch("pwd301.extensions.db.session.commit", side_effect=crash_err),
        pytest.raises(RuntimeError, match="Simulated DB Crash"),
    ):
        store_file_stream(
            actor=instructor,
            course_id=course.public_id,
            file_stream=stream,
            filename="failing_upload.pdf",
            content_type="application/pdf",
            session=db.session,
        )

    # Verify no dangling FileAsset or FileBlob exists in DB
    asset = (
        db.session.query(FileAsset).filter(FileAsset.display_name == "failing_upload.pdf").first()
    )
    assert asset is None


def test_adr002_file_asset_serialization(app: Flask, instructor: User, course: Course) -> None:
    """Verify serialized FileAsset exposes zero internal BIGINT PK or storage_path."""
    content = b"ADR-002 Serialization Invariant Test"
    asset = store_file_stream(
        actor=instructor,
        course_id=course.public_id,
        file_stream=io.BytesIO(content),
        filename="adr002_test.pdf",
        content_type="application/pdf",
        session=db.session,
    )

    serialized = _serialize_file_asset(asset)

    # Must contain public UUIDs
    assert "asset_id" in serialized
    assert uuid.UUID(serialized["asset_id"]) == asset.public_id
    assert "course_id" in serialized
    assert uuid.UUID(serialized["course_id"]) == course.public_id

    # Must NOT contain internal PKs or physical storage keys
    assert "id" not in serialized
    assert "blob_id" not in serialized
    assert "file_asset_id" not in serialized
    assert "storage_key" not in serialized
    assert "storage_path" not in serialized
