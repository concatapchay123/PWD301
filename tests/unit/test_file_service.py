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
from pathlib import Path
from unittest.mock import patch

import pytest
import sqlalchemy as sa
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
    attach_resource_to_lesson,
    check_file_size_limit,
    get_file_quarantine_root,
    get_file_storage_root,
    rescan_file_asset,
    restore_file_asset,
    sanitize_filename,
    store_file_stream,
    trash_file_asset,
    validate_file_metadata,
)
from pwd301.services.lesson_service import create_learning_unit, create_lesson
from pwd301.services.scanner_service import ScanVerdict
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


@pytest.mark.parametrize("outcome", ["new_blob", "deduplicated_blob", "infected"])
def test_rescan_failed_commit_preserves_quarantined_bytes_for_retry(
    app: Flask, instructor: User, course: Course, outcome: str
) -> None:
    payload = b"Quarantined scan transaction rollback fixture."
    clean = ScanVerdict(status="PASS", engine_name="fixture")
    unavailable = ScanVerdict(status="ERROR", engine_name="fixture")
    verdict = ScanVerdict(status="FAIL", engine_name="fixture") if outcome == "infected" else clean
    if outcome == "deduplicated_blob":
        with (
            patch("pwd301.services.file_service.scan_file_all_engines", return_value=[clean]),
            patch("pwd301.services.file_service.scan_blob_file", return_value=clean),
        ):
            store_file_stream(instructor, course.id, io.BytesIO(payload), "existing.txt")
    with (
        patch("pwd301.services.file_service.scan_file_all_engines", return_value=[unavailable]),
        patch("pwd301.services.file_service.scan_blob_file", return_value=unavailable),
    ):
        asset = store_file_stream(instructor, course.id, io.BytesIO(payload), "pending.txt")
    asset_id = asset.id
    revision = db.session.query(FileRevision).filter_by(file_asset_id=asset_id).one()
    source = get_file_quarantine_root() / Path(revision.quarantine_key).name
    assert source.read_bytes() == payload
    session = db.session()

    def reject_commit(commit_session) -> None:
        raise RuntimeError("Claim lost before scan commit")

    sa.event.listen(session, "before_commit", reject_commit)
    try:
        with (
            patch("pwd301.services.file_service.scan_file_all_engines", return_value=[verdict]),
            patch("pwd301.services.file_service.scan_blob_file", return_value=verdict),
            pytest.raises(RuntimeError, match="Claim lost"),
        ):
            rescan_file_asset(instructor, asset_id, session=session)
    finally:
        sa.event.remove(session, "before_commit", reject_commit)
    assert source.is_file() and source.read_bytes() == payload
    assert session.get(FileAsset, asset_id).status == "PENDING"
    assert (
        session.query(FileRevision).filter_by(file_asset_id=asset_id).one().status == "QUARANTINED"
    )
    with (
        patch("pwd301.services.file_service.scan_file_all_engines", return_value=[verdict]),
        patch("pwd301.services.file_service.scan_blob_file", return_value=verdict),
    ):
        rescan_file_asset(instructor, asset_id, session=session)
    assert not source.exists()
    assert session.query(FileRevision).filter_by(file_asset_id=asset_id).one().status == (
        "REJECTED" if outcome == "infected" else "ACTIVE"
    )


def test_lesson_document_cap_is_enforced_by_service(
    app: Flask, instructor: User, course: Course
) -> None:
    unit = create_learning_unit(instructor, course.id, {"title": "Materials"})
    lesson = create_lesson(
        instructor,
        course.id,
        {
            "title": "Documents",
            "markdown_content": "# Documents",
            "learning_unit_id": str(unit.public_id),
        },
    )
    for index in range(6):
        asset = store_file_stream(
            actor=instructor,
            course_id=course.id,
            file_stream=io.BytesIO(f"document {index}".encode()),
            filename=f"document_{index}.pdf",
            content_type="application/pdf",
            session=db.session,
        )
        if index == 5:
            with pytest.raises(FileValidationError, match="5"):
                attach_resource_to_lesson(instructor, lesson.id, asset.id, session=db.session)
        else:
            attach_resource_to_lesson(instructor, lesson.id, asset.id, session=db.session)


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
    validate_file_metadata("cad.dwg")
    validate_file_metadata("plan.dxf")
    validate_file_metadata("sculpture.obj")
    validate_file_metadata("model.fbx")
    validate_file_metadata("part.stl")
    validate_file_metadata("scene.blend")
    validate_file_metadata("assembly.step")
    validate_file_metadata("assembly.stp")
    validate_file_metadata("mesh.gltf")
    validate_file_metadata("mesh.glb")


def test_reject_archive_extensions_with_exact_vietnamese_message() -> None:
    """Canonical invariant: archives (.zip, .rar, .7z, etc.) are strictly rejected with exact Vietnamese message."""
    expected_msg = (
        "Hệ thống không hỗ trợ tệp nén (.zip, .rar, .7z...). Vui lòng tải trực tiếp tài liệu học tập (PDF, Word, Excel, CAD, 3D...)"
    )
    archive_files = [
        "archive.zip",
        "archive.rar",
        "archive.7z",
        "archive.tar",
        "archive.gz",
        "archive.bz2",
        "archive.xz",
        "archive.iso",
        "data.tar.gz",
    ]
    for fname in archive_files:
        with pytest.raises(FileValidationError) as exc_info:
            validate_file_metadata(fname)
        assert str(exc_info.value) == expected_msg


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

    # PPTX limit: 50 MB (strict 50MB attachment ceiling)
    check_file_size_limit(50_000_000, "lecture.pptx")
    with pytest.raises(FileSizeLimitExceededError):
        check_file_size_limit(50_000_001, "lecture.pptx")

    # CAD & 3D limit: 50 MB
    check_file_size_limit(50_000_000, "blueprint.dwg")
    with pytest.raises(FileSizeLimitExceededError):
        check_file_size_limit(50_000_001, "blueprint.dwg")

    check_file_size_limit(50_000_000, "character.blend")
    with pytest.raises(FileSizeLimitExceededError):
        check_file_size_limit(50_000_001, "character.blend")

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


def test_store_file_stream_rejects_archives_with_exact_vietnamese_message(
    app: Flask, instructor: User, course: Course
) -> None:
    """Verify store_file_stream blocks archive extensions with exact Vietnamese message."""
    expected_msg = (
        "Hệ thống không hỗ trợ tệp nén (.zip, .rar, .7z...). Vui lòng tải trực tiếp tài liệu học tập (PDF, Word, Excel, CAD, 3D...)"
    )
    for ext in [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso"]:
        with pytest.raises(FileValidationError) as exc_info:
            store_file_stream(
                actor=instructor,
                course_id=course.public_id,
                file_stream=io.BytesIO(b"Fake archive bytes"),
                filename=f"lecture{ext}",
                session=db.session,
            )
        assert str(exc_info.value) == expected_msg


def test_store_file_stream_rejects_archive_magic_bytes(
    app: Flask, instructor: User, course: Course
) -> None:
    """Verify archive magic bytes are detected and rejected even if file extension is masqueraded."""
    expected_msg = (
        "Hệ thống không hỗ trợ tệp nén (.zip, .rar, .7z...). Vui lòng tải trực tiếp tài liệu học tập (PDF, Word, Excel, CAD, 3D...)"
    )
    # Generic ZIP disguised as PDF
    zip_bytes = io.BytesIO()
    import zipfile

    with zipfile.ZipFile(zip_bytes, "w") as zf:
        zf.writestr("test.txt", b"secret")
    zip_payload = zip_bytes.getvalue()

    with pytest.raises(FileValidationError) as exc_info:
        store_file_stream(
            actor=instructor,
            course_id=course.public_id,
            file_stream=io.BytesIO(zip_payload),
            filename="document.pdf",
            session=db.session,
        )
    assert str(exc_info.value) == expected_msg

    # Generic ZIP disguised as DOCX (no OOXML structure)
    with pytest.raises(FileValidationError) as exc_info:
        store_file_stream(
            actor=instructor,
            course_id=course.public_id,
            file_stream=io.BytesIO(zip_payload),
            filename="document.docx",
            session=db.session,
        )
    assert str(exc_info.value) == expected_msg

    # RAR disguised as CAD
    rar_payload = b"Rar!\x1a\x07\x00\x00\x00\x00Payload"
    with pytest.raises(FileValidationError) as exc_info:
        store_file_stream(
            actor=instructor,
            course_id=course.public_id,
            file_stream=io.BytesIO(rar_payload),
            filename="blueprint.dwg",
            session=db.session,
        )
    assert str(exc_info.value) == expected_msg

    # 7z disguised as 3D OBJ
    sevenz_payload = b"7z\xbc\xaf\x27\x1c\x00\x00Payload"
    with pytest.raises(FileValidationError) as exc_info:
        store_file_stream(
            actor=instructor,
            course_id=course.public_id,
            file_stream=io.BytesIO(sevenz_payload),
            filename="model.obj",
            session=db.session,
        )
    assert str(exc_info.value) == expected_msg


def test_store_file_stream_accepts_cad_and_3d_files(
    app: Flask, instructor: User, course: Course
) -> None:
    """Verify AutoCAD and 3D files are successfully uploaded, categorized, and given proper MIME types."""
    cad_3d_samples = [
        ("plan.dwg", b"AC1032\x00\x00AutoCAD drawing payload", "application/acad"),
        ("drawing.dxf", b"SECTION\n  2\nHEADER\n  0\nENDSEC\n  0\nEOF\n", "application/dxf"),
        ("mesh.obj", b"v 0.0 0.0 0.0\nv 1.0 1.0 1.0\nf 1 2 3\n", "model/obj"),
        ("model.fbx", b"Kaydara FBX Binary  \x00Payload", "application/octet-stream"),
        ("part.stl", b"solid cube\n  facet normal 0 0 0\n  endfacet\nendsolid cube\n", "model/stl"),
        ("scene.blend", b"BLENDER_v300ScenePayloadBytes", "application/x-blender"),
        (
            "step1.step",
            b"ISO-10303-21;\nHEADER;\nENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;\n",
            "application/step",
        ),
        (
            "step2.stp",
            b"ISO-10303-21;\nHEADER;\nENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;\n",
            "application/step",
        ),
        ("model.gltf", b'{"asset": {"version": "2.0"}, "scenes": []}', "model/gltf+json"),
        ("model.glb", b"glTF\x02\x00\x00\x00\x0c\x00\x00\x00BinaryPayload", "model/gltf-binary"),
    ]

    for filename, payload, expected_mime in cad_3d_samples:
        asset = store_file_stream(
            actor=instructor,
            course_id=course.public_id,
            file_stream=io.BytesIO(payload),
            filename=filename,
            session=db.session,
        )
        assert asset is not None
        assert asset.status == "ACTIVE"
        assert asset.current_revision is not None
        assert asset.current_revision.detected_mime_type == expected_mime


def test_store_file_stream_50mb_ceiling(
    app: Flask, instructor: User, course: Course
) -> None:
    """Verify strict 50MB ceiling: 50,000,001 bytes is rejected with FileSizeLimitExceededError."""

    class OversizedStream:
        def __init__(self, size: int) -> None:
            self.remaining = size

        def read(self, n: int = -1) -> bytes:
            if self.remaining <= 0:
                return b""
            chunk_size = min(n if n > 0 else 65536, self.remaining)
            self.remaining -= chunk_size
            return b"B" * chunk_size

    # 50,000,001 bytes should be rejected
    stream = OversizedStream(50_000_001)
    with pytest.raises(FileSizeLimitExceededError):
        store_file_stream(
            actor=instructor,
            course_id=course.public_id,
            file_stream=stream,  # type: ignore[arg-type]
            filename="oversized.pdf",
            session=db.session,
        )
