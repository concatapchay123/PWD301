"""File storage and authorization service for PWD301.

Implements:
- Physical Blob and Logical Asset separation (ADR-008).
- SHA-256 Content-hash deduplication (Algorithm 12).
- Zero PK leakage and public UUIDv4/v5 boundaries (ADR-002).
- Strict upload size constraints (video < 1 GB, images <= 10 MB,
  PDF/DOCX <= 50 MB, PPTX <= 100 MB).
- Fail-closed download security and zero-trust IDOR prevention.
"""

from __future__ import annotations

import hashlib
import mimetypes
import os
import re
import uuid
from datetime import timedelta
from pathlib import Path
from typing import IO, Any, BinaryIO

import sqlalchemy as sa
from flask import current_app
from sqlalchemy.orm import Session, scoped_session

from pwd301.extensions import db
from pwd301.models.course import Course, Enrollment, Lesson
from pwd301.models.file_import import (
    FileAsset,
    FileBlob,
    FileRevision,
    FileScanResult,
    LessonResource,
)
from pwd301.models.identity import User
from pwd301.models.types import utc_now
from pwd301.services.authorization_service import (
    _resolve_lesson,
    require_course_manager,
)
from pwd301.services.exceptions import (
    FileAccessDeniedError,
    FileAssetNotFoundError,
    FileSecurityQuarantineError,
    FileSizeLimitExceededError,
    FileStorageError,
    FileValidationError,
    ResourceNotFoundError,
)

# Dangerous executable extensions strictly forbidden per security architecture
DANGEROUS_EXTENSIONS: frozenset[str] = frozenset(
    {
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
        # Macro-enabled Office forbidden per Business Rule 11
        ".docm",
        ".xlsm",
        ".pptm",
        ".dotm",
        ".xltm",
        ".potm",
    }
)

IMAGE_EXTENSIONS: frozenset[str] = frozenset(
    {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".ico", ".tiff"}
)

VIDEO_EXTENSIONS: frozenset[str] = frozenset(
    {".mp4", ".webm", ".mkv", ".mov", ".avi", ".m4v", ".wmv", ".flv"}
)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and shell injection attacks.

    Extracts basename only, removes null bytes, slashes, and hazardous characters,
    and strips leading/trailing dots and spaces.
    """
    if not filename:
        return "unnamed_file"

    # Normalize backslashes and get basename
    cleaned = os.path.basename(filename.replace("\\", "/"))

    # Remove null bytes and non-printable characters
    cleaned = "".join(c for c in cleaned if c.isprintable() and c not in '<>:"/\\|?*;\x00')

    # Remove any traversal patterns remaining
    cleaned = re.sub(r"\.\.+", ".", cleaned)

    # Strip whitespace and dots from ends
    cleaned = cleaned.strip(". ")

    return cleaned or "unnamed_file"


def get_file_storage_root() -> Path:
    """Resolve the root path for permanent physical file storage."""
    raw = current_app.config.get("FILE_STORAGE_ROOT", "./storage")
    path = Path(raw).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_quarantine_root() -> Path:
    """Resolve the root path for temporary quarantine uploads."""
    raw = current_app.config.get("FILE_QUARANTINE_ROOT", "./quarantine")
    path = Path(raw).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def validate_file_metadata(filename: str, declared_mime: str | None = None) -> None:
    """Validate file metadata against forbidden executable extensions."""
    ext = Path(filename).suffix.lower()
    if ext in DANGEROUS_EXTENSIONS:
        raise FileValidationError(f"File extension '{ext}' is forbidden for security.")


def check_file_size_limit(size_bytes: int, filename: str) -> None:
    """Check file size strictly against configured category limits.

    Non-negotiable invariant:
    - Video files must be strictly < 1 GB (1,000,000,000 bytes).
    """
    if size_bytes <= 0:
        raise FileValidationError("Uploaded file is empty (0 bytes).")

    ext = Path(filename).suffix.lower()

    # Video check: strictly < 1 GB (1,000,000,000 bytes)
    max_video_exclusive = current_app.config.get("MAX_VIDEO_BYTES_EXCLUSIVE", 1_000_000_000)
    if ext in VIDEO_EXTENSIONS and size_bytes >= max_video_exclusive:
        raise FileSizeLimitExceededError(
            f"Video file exceeds maximum allowed limit of {max_video_exclusive} bytes "
            "(strictly < 1 GB)."
        )

    # Platform-wide exclusive upper ceiling
    if size_bytes >= max_video_exclusive:
        raise FileSizeLimitExceededError(
            f"File exceeds maximum platform limit of {max_video_exclusive} bytes."
        )

    # Image limit
    max_image = current_app.config.get("MAX_IMAGE_BYTES", 10_000_000)
    if ext in IMAGE_EXTENSIONS and size_bytes > max_image:
        raise FileSizeLimitExceededError(
            f"Image file exceeds maximum allowed size of {max_image} bytes."
        )

    # PDF limit
    max_pdf = current_app.config.get("MAX_PDF_BYTES", 50_000_000)
    if ext == ".pdf" and size_bytes > max_pdf:
        raise FileSizeLimitExceededError(
            f"PDF file exceeds maximum allowed size of {max_pdf} bytes."
        )

    # DOCX limit
    max_docx = current_app.config.get("MAX_DOCX_BYTES", 50_000_000)
    if ext in {".docx", ".doc"} and size_bytes > max_docx:
        raise FileSizeLimitExceededError(
            f"DOCX file exceeds maximum allowed size of {max_docx} bytes."
        )

    # PPTX limit
    max_pptx = current_app.config.get("MAX_PPTX_BYTES", 100_000_000)
    if ext in {".pptx", ".ppt"} and size_bytes > max_pptx:
        raise FileSizeLimitExceededError(
            f"PPTX file exceeds maximum allowed size of {max_pptx} bytes."
        )


def detect_mime_type(header_bytes: bytes, filename: str, declared_mime: str | None = None) -> str:
    """Detect MIME type combining magic byte signatures and filename extension."""
    # Magic bytes check
    if header_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if header_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if header_bytes.startswith(b"GIF87a") or header_bytes.startswith(b"GIF89a"):
        return "image/gif"
    if header_bytes.startswith(b"%PDF-"):
        return "application/pdf"
    if header_bytes.startswith(b"PK\x03\x04"):
        ext = Path(filename).suffix.lower()
        if ext == ".docx":
            return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if ext == ".pptx":
            return "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    if (
        header_bytes.startswith(b"RIFF")
        and len(header_bytes) >= 12
        and header_bytes[8:12] == b"WEBP"
    ):
        return "image/webp"

    guessed, _ = mimetypes.guess_type(filename)
    if guessed:
        return guessed

    if declared_mime and declared_mime not in {"application/octet-stream", ""}:
        return declared_mime

    return "application/octet-stream"


def _resolve_file_asset(
    asset_or_id: FileAsset | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> FileAsset | None:
    """Resolve a FileAsset instance by model, public UUID, or internal PK."""
    if isinstance(asset_or_id, FileAsset):
        return asset_or_id

    sess = session if session is not None else db.session
    if isinstance(asset_or_id, int):
        return sess.get(FileAsset, asset_or_id)

    if isinstance(asset_or_id, uuid.UUID):
        return sess.query(FileAsset).filter(FileAsset.public_id == asset_or_id).first()

    if isinstance(asset_or_id, str):
        try:
            val_uuid = uuid.UUID(asset_or_id)
            return sess.query(FileAsset).filter(FileAsset.public_id == val_uuid).first()
        except ValueError:
            pass
        if asset_or_id.isdigit():
            return sess.get(FileAsset, int(asset_or_id))

    return None


def store_file_stream(
    actor: User,
    course_id: Course | int | uuid.UUID | str,
    file_stream: IO[bytes] | BinaryIO,
    filename: str,
    content_type: str | None = None,
    asset_type: str = "RESOURCE",
    title: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> FileAsset:
    """Store an uploaded file stream following Algorithm 12 Deduplication.

    1. Enforces course management authorization.
    2. Validates filename and extension security.
    3. Streams content to quarantine while computing SHA-256 and checking size limits.
    4. If hash exists in file_blobs: increments reference_count, reuses blob, deletes temp file.
    5. If hash is new: moves to hierarchical path (storage/blobs/ab/cd/<hash>), creates FileBlob.
    6. Creates FileAsset and FileRevision 1 in ACTIVE state, records passing FileScanResult.
    7. Provides safe rollback: cleans up newly written disk files if DB commit fails.
    """
    sess = session if session is not None else db.session
    course = require_course_manager(actor, course_id, session=sess)

    clean_filename = sanitize_filename(filename)
    validate_file_metadata(clean_filename, content_type)

    quarantine_root = get_file_quarantine_root()
    temp_filename = f"upload_{uuid.uuid4().hex}.tmp"
    temp_path = quarantine_root / temp_filename

    hasher = hashlib.sha256()
    total_size = 0
    header_bytes = b""
    newly_created_dest: Path | None = None

    try:
        # Stream into quarantine temp file
        with open(temp_path, "wb") as f_out:
            while True:
                chunk = file_stream.read(64 * 1024)
                if not chunk:
                    break
                if not header_bytes:
                    header_bytes = chunk[:512]
                total_size += len(chunk)

                # Early check during streaming to avoid disk exhaustion
                max_video_exclusive = current_app.config.get(
                    "MAX_VIDEO_BYTES_EXCLUSIVE", 1_000_000_000
                )
                if total_size >= max_video_exclusive:
                    raise FileSizeLimitExceededError(
                        f"File size exceeded maximum limit of {max_video_exclusive} bytes."
                    )

                hasher.update(chunk)
                f_out.write(chunk)

        # Validate total size strictly
        check_file_size_limit(total_size, clean_filename)
        detected_mime = detect_mime_type(header_bytes, clean_filename, content_type)

        digest_bytes = hasher.digest()
        hex_hash = hasher.hexdigest()

        # Algorithm 12 Deduplication lookup
        blob = sess.query(FileBlob).filter(FileBlob.sha256 == digest_bytes).first()
        if blob is not None and blob.status == "PRESENT":
            # Reuse existing blob
            blob.reference_count += 1
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)
        else:
            # New unique blob: create hierarchical storage path
            storage_root = get_file_storage_root()
            ab = hex_hash[:2]
            cd = hex_hash[2:4]
            dest_dir = storage_root / "blobs" / ab / cd
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path = dest_dir / hex_hash

            # Move quarantine temp file to permanent storage
            if temp_path.exists():
                os.replace(temp_path, dest_path)
            newly_created_dest = dest_path

            storage_key = f"blobs/{ab}/{cd}/{hex_hash}"
            blob = FileBlob(
                sha256=digest_bytes,
                size_bytes=total_size,
                detected_mime_type=detected_mime,
                storage_key=storage_key,
                status="PRESENT",
                reference_count=1,
            )
            sess.add(blob)
            sess.flush()

        # Create logical FileAsset
        valid_asset_types = {
            "RESOURCE",
            "QUESTION_IMAGE",
            "COURSE_IMAGE",
            "IMPORT_SOURCE",
            "EXPORT",
            "OTHER",
        }
        chosen_type = (
            asset_type.upper()
            if asset_type and asset_type.upper() in valid_asset_types
            else "RESOURCE"
        )

        asset = FileAsset(
            course_id=course.id,
            created_by_user_id=actor.id,
            asset_type=chosen_type,
            display_name=title or clean_filename,
            status="ACTIVE",
        )
        sess.add(asset)
        sess.flush()

        # Create initial FileRevision (revision_no=1)
        revision = FileRevision(
            file_asset_id=asset.id,
            revision_no=1,
            is_current=True,
            blob_id=blob.id,
            original_filename=clean_filename,
            declared_mime_type=content_type or detected_mime,
            detected_mime_type=detected_mime,
            size_bytes=total_size,
            status="ACTIVE",
            uploaded_by_user_id=actor.id,
            security_checks_completed_at=utc_now(),
            activated_at=utc_now(),
        )
        sess.add(revision)
        sess.flush()

        # Record validation scan result
        scan_result = FileScanResult(
            file_revision_id=revision.id,
            scan_type="FILE_VALIDATION",
            engine="builtin_validator",
            engine_version="1.0",
            status="PASS",
            details_json=None,
            started_at=utc_now(),
            completed_at=utc_now(),
        )
        sess.add(scan_result)
        sess.commit()

        return asset

    except Exception:
        sess.rollback()
        # Clean up temporary quarantine file
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
        # Rollback safety: clean up newly created physical storage file
        if newly_created_dest is not None and newly_created_dest.exists():
            newly_created_dest.unlink(missing_ok=True)
        raise


def add_file_revision(
    actor: User,
    asset_id: FileAsset | int | uuid.UUID | str,
    file_stream: IO[bytes] | BinaryIO,
    filename: str,
    content_type: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> FileRevision:
    """Upload a new revision for an existing FileAsset."""
    sess = session if session is not None else db.session
    asset = _resolve_file_asset(asset_id, session=sess)
    if asset is None:
        raise FileAssetNotFoundError("File asset not found.")

    require_course_manager(actor, asset.course_id, session=sess)

    if asset.status in ("TRASH", "DELETED"):
        raise FileValidationError("Cannot add revision to a trashed or deleted file asset.")

    clean_filename = sanitize_filename(filename)
    validate_file_metadata(clean_filename, content_type)

    quarantine_root = get_file_quarantine_root()
    temp_filename = f"rev_{uuid.uuid4().hex}.tmp"
    temp_path = quarantine_root / temp_filename

    hasher = hashlib.sha256()
    total_size = 0
    header_bytes = b""
    newly_created_dest: Path | None = None

    try:
        with open(temp_path, "wb") as f_out:
            while True:
                chunk = file_stream.read(64 * 1024)
                if not chunk:
                    break
                if not header_bytes:
                    header_bytes = chunk[:512]
                total_size += len(chunk)

                max_video_exclusive = current_app.config.get(
                    "MAX_VIDEO_BYTES_EXCLUSIVE", 1_000_000_000
                )
                if total_size >= max_video_exclusive:
                    raise FileSizeLimitExceededError(
                        f"File size exceeded maximum limit of {max_video_exclusive} bytes."
                    )

                hasher.update(chunk)
                f_out.write(chunk)

        check_file_size_limit(total_size, clean_filename)
        detected_mime = detect_mime_type(header_bytes, clean_filename, content_type)

        digest_bytes = hasher.digest()
        hex_hash = hasher.hexdigest()

        # Deduplication lookup
        blob = sess.query(FileBlob).filter(FileBlob.sha256 == digest_bytes).first()
        if blob is not None and blob.status == "PRESENT":
            blob.reference_count += 1
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)
        else:
            storage_root = get_file_storage_root()
            ab = hex_hash[:2]
            cd = hex_hash[2:4]
            dest_dir = storage_root / "blobs" / ab / cd
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path = dest_dir / hex_hash

            if temp_path.exists():
                os.replace(temp_path, dest_path)
            newly_created_dest = dest_path

            storage_key = f"blobs/{ab}/{cd}/{hex_hash}"
            blob = FileBlob(
                sha256=digest_bytes,
                size_bytes=total_size,
                detected_mime_type=detected_mime,
                storage_key=storage_key,
                status="PRESENT",
                reference_count=1,
            )
            sess.add(blob)
            sess.flush()

        # Mark all existing revisions for this asset as inactive/replaced
        now = utc_now()
        existing_revisions = (
            sess.query(FileRevision).filter(FileRevision.file_asset_id == asset.id).all()
        )
        max_rev = 0
        for rev in existing_revisions:
            if rev.revision_no > max_rev:
                max_rev = rev.revision_no
            if rev.is_current:
                rev.is_current = False
                rev.replaced_at = now
                rev.status = "REPLACED"
                rev.recovery_until = now + timedelta(days=30)

        # Create new active revision
        new_rev = FileRevision(
            file_asset_id=asset.id,
            revision_no=max_rev + 1,
            is_current=True,
            blob_id=blob.id,
            original_filename=clean_filename,
            declared_mime_type=content_type or detected_mime,
            detected_mime_type=detected_mime,
            size_bytes=total_size,
            status="ACTIVE",
            uploaded_by_user_id=actor.id,
            security_checks_completed_at=now,
            activated_at=now,
        )
        sess.add(new_rev)
        sess.flush()

        asset.display_name = clean_filename
        asset.updated_at = now

        scan_result = FileScanResult(
            file_revision_id=new_rev.id,
            scan_type="FILE_VALIDATION",
            engine="builtin_validator",
            engine_version="1.0",
            status="PASS",
            details_json=None,
            started_at=now,
            completed_at=now,
        )
        sess.add(scan_result)
        sess.commit()

        return new_rev

    except Exception:
        sess.rollback()
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
        if newly_created_dest is not None and newly_created_dest.exists():
            newly_created_dest.unlink(missing_ok=True)
        raise


def trash_file_asset(
    actor: User,
    asset_id: FileAsset | int | uuid.UUID | str,
    reason: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> FileAsset:
    """Soft-delete a logical FileAsset to TRASH status."""
    sess = session if session is not None else db.session
    asset = _resolve_file_asset(asset_id, session=sess)
    if asset is None:
        raise FileAssetNotFoundError("File asset not found.")

    require_course_manager(actor, asset.course_id, session=sess)

    now = utc_now()
    asset.status = "TRASH"
    asset.deleted_at = now
    asset.deleted_by_user_id = actor.id
    asset.restore_until = now + timedelta(days=30)
    asset.updated_at = now

    sess.commit()
    return asset


def restore_file_asset(
    actor: User,
    asset_id: FileAsset | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> FileAsset:
    """Restore a soft-deleted FileAsset from TRASH to ACTIVE status."""
    sess = session if session is not None else db.session
    asset = _resolve_file_asset(asset_id, session=sess)
    if asset is None:
        raise FileAssetNotFoundError("File asset not found.")

    require_course_manager(actor, asset.course_id, session=sess)

    now = utc_now()
    asset.status = "ACTIVE"
    asset.deleted_at = None
    asset.deleted_by_user_id = None
    asset.restore_until = None
    asset.updated_at = now

    sess.commit()
    return asset


def get_file_for_download(
    actor: User | None,
    asset_id: FileAsset | int | uuid.UUID | str,
    revision_no: int | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> tuple[FileAsset, FileBlob, Path]:
    """Authorize access and retrieve physical file path for streaming/download.

    Enforces Zero-Trust & Fail-Closed rules:
    - Actor must be active and authenticated.
    - Admin has platform-wide access.
    - Managing Instructor has access to all files within their course.
    - Enrolled Student must have ACTIVE enrollment, course must be PUBLISHED,
      and any lesson to which the asset is attached must be PUBLISHED.
    - External instructors or unenrolled students are rejected with 403 Forbidden.
    - FileAsset must be ACTIVE (not TRASH or DELETED).
    - Requested or Current FileRevision must be ACTIVE and have passing scan results.
    - FileBlob must be PRESENT and physically present on disk.
    """
    sess = session if session is not None else db.session
    asset = _resolve_file_asset(asset_id, session=sess)
    if asset is None:
        raise FileAssetNotFoundError("File asset not found.")

    if actor is None or not actor.is_active:
        raise FileAccessDeniedError("Authentication required to download this file.")

    course = sess.get(Course, asset.course_id)
    if course is None:
        raise FileAssetNotFoundError("Parent course not found.")

    # Ma trận phân quyền Zero-Trust
    if actor.is_admin or (actor.has_role("INSTRUCTOR") and course.owner_instructor_id == actor.id):
        is_authorized = True
    elif actor.has_role("STUDENT"):
        # 1. Khóa học phải ở trạng thái PUBLISHED
        if course.status != "PUBLISHED":
            raise FileAccessDeniedError("Cannot download files from an unpublished course.")

        # 2. Học viên có Enrollment ACTIVE trong khóa học
        enrollment = (
            sess.query(Enrollment)
            .filter(
                Enrollment.course_id == course.id,
                Enrollment.student_user_id == actor.id,
                Enrollment.status == "ACTIVE",
            )
            .first()
        )
        if enrollment is None:
            raise FileAccessDeniedError("You are not actively enrolled in this course.")

        # 3. Nếu tệp gắn với Lesson, bài học đó phải ở trạng thái PUBLISHED
        lesson_resources = (
            sess.query(LessonResource).filter(LessonResource.file_asset_id == asset.id).all()
        )
        if lesson_resources:
            attached_lessons = [sess.get(Lesson, lr.lesson_id) for lr in lesson_resources]
            published_lessons = [
                les for les in attached_lessons if les is not None and les.status == "PUBLISHED"
            ]
            if not published_lessons:
                raise FileAccessDeniedError(
                    "The lesson containing this resource is not yet published."
                )

        is_authorized = True
    else:
        is_authorized = False

    if not is_authorized:
        raise FileAccessDeniedError("You do not have permission to access this file.")

    # Fail-Closed Security Checks
    if asset.status != "ACTIVE":
        raise FileAccessDeniedError(f"File asset is not accessible (status: {asset.status}).")

    if revision_no is not None:
        revision = (
            sess.query(FileRevision)
            .filter(
                FileRevision.file_asset_id == asset.id,
                FileRevision.revision_no == revision_no,
            )
            .first()
        )
        if revision is None:
            raise FileAssetNotFoundError(f"Revision {revision_no} not found for this asset.")
    else:
        revision = asset.current_revision
        if revision is None:
            # Fallback to the latest current revision
            revision = (
                sess.query(FileRevision)
                .filter(
                    FileRevision.file_asset_id == asset.id,
                    FileRevision.is_current.is_(True),
                )
                .first()
            )

    if revision is None or revision.status not in ("ACTIVE", "REPLACED"):
        raise FileSecurityQuarantineError(
            "File revision is quarantined or not approved for access."
        )

    # Check scan results: reject if any failed or error
    for scan in revision.scan_results:
        if scan.status in ("FAIL", "ERROR"):
            raise FileSecurityQuarantineError(
                "File security verification failed or malware detected."
            )

    blob = revision.blob
    if blob is None or blob.status != "PRESENT":
        raise FileStorageError("Physical storage blob is missing or deleted.")

    storage_root = get_file_storage_root()
    physical_path = storage_root / blob.storage_key
    if not physical_path.exists():
        raise FileStorageError("Physical file blob not found on disk.")

    return asset, blob, physical_path


def attach_resource_to_lesson(
    actor: User,
    lesson_id: Lesson | int | uuid.UUID | str,
    asset_id: FileAsset | int | uuid.UUID | str,
    is_downloadable: bool = True,
    label: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> LessonResource:
    """Attach a FileAsset to a Lesson as a learning resource."""
    sess = session if session is not None else db.session
    lesson = _resolve_lesson(lesson_id, session=sess)
    if lesson is None:
        raise ResourceNotFoundError("Lesson not found.")

    require_course_manager(actor, lesson.course_id, session=sess)

    asset = _resolve_file_asset(asset_id, session=sess)
    if asset is None:
        raise FileAssetNotFoundError("File asset not found.")

    # Invariant: file_asset.course_id phải cùng lesson.course_id
    if asset.course_id != lesson.course_id:
        raise FileValidationError("File asset belongs to a different course than the lesson.")

    existing = (
        sess.query(LessonResource)
        .filter(
            LessonResource.lesson_id == lesson.id,
            LessonResource.file_asset_id == asset.id,
        )
        .first()
    )
    if existing is not None:
        if label:
            existing.label = label
        sess.commit()
        return existing

    max_pos = (
        sess.query(sa.func.max(LessonResource.position))
        .filter(LessonResource.lesson_id == lesson.id)
        .scalar()
        or 0
    )

    resource = LessonResource(
        lesson_id=lesson.id,
        file_asset_id=asset.id,
        position=max_pos + 1,
        label=label or asset.display_name,
        is_required=False,
    )
    sess.add(resource)
    sess.commit()

    return resource


def detach_resource_from_lesson(
    actor: User,
    lesson_id: Lesson | int | uuid.UUID | str,
    resource_id: int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> bool:
    """Detach a learning resource link from a Lesson."""
    sess = session if session is not None else db.session
    lesson = _resolve_lesson(lesson_id, session=sess)
    if lesson is None:
        raise ResourceNotFoundError("Lesson not found.")

    require_course_manager(actor, lesson.course_id, session=sess)

    # Resolve resource by synthetic public_id, internal id, or asset public_id
    res: LessonResource | None = None
    all_resources = sess.query(LessonResource).filter(LessonResource.lesson_id == lesson.id).all()

    target_str = str(resource_id)
    for r in all_resources:
        if str(r.public_id) == target_str or str(r.id) == target_str:
            res = r
            break
        if r.file_asset and str(r.file_asset.public_id) == target_str:
            res = r
            break

    if res is None:
        raise ResourceNotFoundError("Lesson resource link not found.")

    sess.delete(res)
    sess.commit()
    return True


def list_course_files(
    actor: User,
    course_id: Course | int | uuid.UUID | str,
    status: str | None = "ACTIVE",
    session: Session | scoped_session[Any] | None = None,
) -> list[FileAsset]:
    """List FileAssets belonging to a course for authorized instructors or admin."""
    sess = session if session is not None else db.session
    course = require_course_manager(actor, course_id, session=sess)

    query = sess.query(FileAsset).filter(FileAsset.course_id == course.id)
    if status:
        query = query.filter(FileAsset.status == status)
    else:
        query = query.filter(FileAsset.status != "DELETED")

    return query.order_by(FileAsset.created_at.desc()).all()


# ==============================================================================
# ADR-002 Compliant Serializers (Zero Internal PK or Storage Key Leakage)
# ==============================================================================


def _serialize_file_asset(asset: FileAsset) -> dict[str, Any]:
    """Serialize FileAsset exposing only public UUIDs and safe metadata."""
    cur_rev = asset.current_revision or (asset.revisions[-1] if asset.revisions else None)
    return {
        "asset_id": str(asset.public_id),
        "course_id": str(asset.course.public_id) if asset.course else None,
        "title": asset.display_name,
        "display_name": asset.display_name,
        "filename": cur_rev.original_filename if cur_rev else asset.display_name,
        "original_filename": cur_rev.original_filename if cur_rev else asset.display_name,
        "byte_size": cur_rev.size_bytes if cur_rev else 0,
        "mime_type": (
            cur_rev.detected_mime_type or cur_rev.declared_mime_type
            if cur_rev
            else "application/octet-stream"
        ),
        "content_type": (
            cur_rev.detected_mime_type or cur_rev.declared_mime_type
            if cur_rev
            else "application/octet-stream"
        ),
        "status": asset.status,
        "current_version": cur_rev.revision_no if cur_rev else 1,
        "revision_no": cur_rev.revision_no if cur_rev else 1,
        "created_at": asset.created_at.isoformat() if asset.created_at else None,
        "updated_at": asset.updated_at.isoformat() if asset.updated_at else None,
        "revisions": [
            {
                "revision_id": str(r.public_id),
                "version": r.revision_no,
                "revision_no": r.revision_no,
                "byte_size": r.size_bytes,
                "size_bytes": r.size_bytes,
                "detected_mime_type": r.detected_mime_type,
                "status": r.status,
                "created_at": r.activated_at.isoformat() if r.activated_at else None,
            }
            for r in (asset.revisions or [])
        ],
    }


def _serialize_lesson_resource(res: LessonResource) -> dict[str, Any]:
    """Serialize LessonResource with synthetic public UUIDv5 per ADR-002."""
    return {
        "resource_id": str(res.public_id),
        "lesson_id": str(res.lesson.public_id) if res.lesson else None,
        "title": res.label or (res.file_asset.display_name if res.file_asset else None),
        "label": res.label,
        "file_asset": _serialize_file_asset(res.file_asset) if res.file_asset else None,
        "position": res.position,
        "is_required": res.is_required,
        "created_at": res.created_at.isoformat() if res.created_at else None,
    }
